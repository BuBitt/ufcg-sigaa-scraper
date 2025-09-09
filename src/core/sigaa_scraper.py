"""
Classe principal do SIGAA Scraper refatorado.

Coordena serviços para extração e monitoramento de notas do SIGAA da UFCG.
"""

import sys
from typing import List, Dict, Any

from playwright.sync_api import sync_playwright, Page

from src.config.settings import Config
from src.services.auth_service import AuthService
from src.services.navigation_service import NavigationService
from src.services.grade_extractor import GradeExtractor
from src.services.cache_service import CacheService
from src.services.comparison_service import ComparisonService
from src.notifications.telegram_notifier import TelegramNotifier
from src.utils.logger import (
    setup_logger,
    get_logger,
    get_performance_logger,
    log_system_info,
    log_environment_vars,
)
from src.utils.env_loader import load_environment


class SIGAAScraper:
    """Coordenador do processo de scraping do SIGAA."""

    def __init__(self, debug_mode: bool = False) -> None:
        # Configuração de logging
        setup_logger(enable_debug=debug_mode)
        self.logger = get_logger("main")
        self.perf_logger = get_performance_logger()

        self.logger.info(f"Inicializando {Config.APP_NAME} v{Config.VERSION}")

        if debug_mode:
            self.logger.debug("Modo debug habilitado")
            log_system_info()
            log_environment_vars()

        # Ambiente
        if not load_environment():
            self.logger.warning("Arquivo .env não encontrado, usando configurações padrão")

        # Serviços
        self.logger.debug("Inicializando serviços...")
        self._init_services()
        self.logger.info("Todos os serviços inicializados")

    def _init_services(self) -> None:
        self.auth_service = AuthService()
        self.navigation_service = NavigationService()
        self.grade_extractor = GradeExtractor()
        self.cache_service = CacheService()
        self.comparison_service = ComparisonService()
        self.notifier = TelegramNotifier()

    def run(self) -> List[str]:
        """Executa o scraping completo e retorna lista de mudanças."""
        self.logger.info(
            f"Iniciando processo de scraping usando método: {Config.get_extraction_method()}"
        )
        self.perf_logger.start_timer("scraping_total")

        with sync_playwright() as playwright:
            self.logger.debug("Iniciando navegador")
            self.perf_logger.start_timer("browser_setup")

            browser = playwright.chromium.launch(
                headless=Config.HEADLESS_BROWSER,
                slow_mo=500 if not Config.HEADLESS_BROWSER else 0,
            )
            context = browser.new_context(
                viewport={"width": Config.VIEWPORT_WIDTH, "height": Config.VIEWPORT_HEIGHT},
                user_agent=(
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
            )
            page = context.new_page()

            self.perf_logger.end_timer("browser_setup")
            self.logger.debug("Navegador configurado")

            try:
                # Autenticação
                self.perf_logger.start_timer("authentication")
                if not self.auth_service.login(page):
                    raise Exception("Falha na autenticação")
                auth_time = self.perf_logger.end_timer("authentication")

                # Navegação
                self.perf_logger.start_timer("navigation")
                if not self.navigation_service.navigate_to_grades(page):
                    raise Exception("Falha na navegação para seção de notas")
                nav_time = self.perf_logger.end_timer("navigation")

                # Extração
                self.perf_logger.start_timer("extraction")
                grades = self._extract_grades_by_method(page)
                extract_time = self.perf_logger.end_timer("extraction")

                if not grades:
                    self.logger.error("Nenhuma nota extraída")
                    raise Exception("Nenhuma nota extraída")

                self.logger.info("Dados extraídos com sucesso")

                # Comparação
                self.perf_logger.start_timer("comparison")
                old_cache = self.cache_service.load_cache()
                changes_detected = self.comparison_service.compare_grades(old_cache, grades)
                comp_time = self.perf_logger.end_timer("comparison")

                # Cache
                self.perf_logger.start_timer("cache_save")
                try:
                    grades_list = self._convert_grades_to_list(grades)
                    self.cache_service.save_cache(grades_list)
                    cache_time = self.perf_logger.end_timer("cache_save")
                except Exception as cache_error:
                    cache_time = self.perf_logger.end_timer("cache_save")
                    self.logger.error(f"Falha crítica ao salvar cache: {cache_error}")
                    self.logger.warning(
                        "Continuando sem atualizar cache - dados anteriores preservados"
                    )

                # Resumo
                total_time = self.perf_logger.end_timer("scraping_total")
                self._log_performance_summary(
                    auth_time, nav_time, extract_time, comp_time, cache_time, total_time
                )

                self.logger.info(
                    f"Processo concluído! {len(changes_detected)} mudança(s) detectada(s)"
                )
                return changes_detected

            except Exception as e:
                self.logger.error(f"Erro no processo de scraping: {e}")
                self._save_debug_screenshot(page)
                raise
            finally:
                self.logger.debug("Fechando navegador")
                browser.close()

    def _extract_grades_by_method(self, page: Page) -> Dict[str, Any]:
        method = Config.get_extraction_method()
        self.logger.info(f"Método de extração selecionado: {method}")

        if method == "menu_ensino":
            return self._extract_via_menu_ensino(page)
        elif method == "materia_individual":
            return self._extract_via_materia_individual(page)
        else:
            raise ValueError(
                f"Método de extração inválido: {method}. Use 'menu_ensino' ou 'materia_individual'."
            )

    def _extract_via_menu_ensino(self, page: Page) -> Dict[str, Any]:
        self.logger.info("Extraindo notas via menu ensino")
        return self.grade_extractor.extract_from_page_direct(page)

    def _extract_via_materia_individual(self, page: Page) -> Dict[str, Any]:
        self.logger.info("Extraindo notas via matéria individual")

        all_grades: Dict[str, Any] = {}
        components = self.navigation_service.get_available_components(page)

        if not components:
            self.logger.warning("Nenhum componente curricular encontrado")
            return all_grades

        self.logger.info(f"Processando {len(components)} componente(s)")

        for index, component_name in enumerate(components):
            try:
                self.logger.info(
                    f"Processando ({index + 1}/{len(components)}): {component_name}"
                )

                if self.navigation_service.navigate_to_component_grades(page, index):
                    component_grades = self.grade_extractor.extract_from_page_direct(page)

                    if component_grades:
                        all_grades[component_name] = component_grades
                        self.logger.debug(f"Notas extraídas para {component_name}")
                    else:
                        self.logger.warning(
                            f"Nenhuma nota encontrada para {component_name}"
                        )

                    if not self.navigation_service.go_back_to_main(page):
                        self.logger.warning(
                            f"Falha ao voltar à página principal após {component_name}"
                        )
                        break
                else:
                    self.logger.warning(f"Falha ao navegar para {component_name}")
            except Exception as e:
                self.logger.error(f"Erro ao processar {component_name}: {e}")
                try:
                    self.navigation_service.go_back_to_main(page)
                except Exception:
                    pass
                continue

        self.logger.info(
            f"Processamento concluído: {len(all_grades)} matéria(s) com notas"
        )
        return all_grades

    def _convert_grades_to_list(self, grades: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not grades:
            self.logger.warning("Estrutura de notas vazia para conversão")
            return []

        grades_list: List[Dict[str, Any]] = []
        try:
            for section_key, section_data in grades.items():
                if isinstance(section_data, list):
                    for record in section_data:
                        if isinstance(record, dict):
                            record_copy = record.copy()
                            record_copy["_secao"] = section_key
                            grades_list.append(record_copy)
                        else:
                            self.logger.warning(
                                f"Registro inválido ignorado em {section_key}: {type(record)}"
                            )
                elif isinstance(section_data, dict):
                    record_copy = section_data.copy()
                    record_copy["_secao"] = section_key
                    grades_list.append(record_copy)
                else:
                    self.logger.warning(
                        f"Seção inválida ignorada: {section_key} ({type(section_data)})"
                    )

            if not grades_list:
                self.logger.error(
                    "Conversão resultou em lista vazia - dados podem estar corrompidos"
                )
                raise Exception("Falha crítica na conversão de dados de notas")

            self.logger.debug(
                f"Conversão concluída: {len(grades_list)} registro(s)"
            )
            return grades_list
        except Exception as e:
            self.logger.error(f"Erro crítico na conversão para lista: {e}")
            self.logger.error(
                f"Estrutura recebida: {type(grades)} com {len(grades) if hasattr(grades, '__len__') else 0} item(s)"
            )
            raise Exception(f"Falha na conversão de cache: {e}") from e

    def _log_performance_summary(
        self,
        auth_time: float,
        nav_time: float,
        extract_time: float,
        comp_time: float,
        cache_time: float,
        total_time: float,
    ) -> None:
        """Registra resumo de performance."""
        self.logger.info("Resumo de Performance:")
        self.logger.info(f"   Autenticação: {auth_time:.2f}s")
        self.logger.info(f"   Navegação: {nav_time:.2f}s")
        self.logger.info(f"   Extração: {extract_time:.2f}s")
        self.logger.info(f"   Comparação: {comp_time:.2f}s")
        self.logger.info(f"   Cache: {cache_time:.2f}s")
        self.logger.info(f"   Total: {total_time:.2f}s")

    def _save_debug_screenshot(self, page: Page) -> None:
        try:
            self.logger.debug("Salvando screenshot para debug...")
            page.screenshot(path="logs/error_screenshot.png")
            self.logger.debug("Screenshot salvo em logs/error_screenshot.png")
        except Exception as e:
            self.logger.warning(f"Erro ao salvar screenshot: {e}")

    def test_configuration(self) -> bool:
        try:
            self.logger.info("Testando configuração do sistema")

            if not load_environment():
                self.logger.warning("Arquivo .env não encontrado")

            try:
                self.auth_service.env_loader.validate_credentials()
                self.logger.info("Credenciais SIGAA válidas")
            except Exception as e:
                self.logger.error(f"Credenciais inválidas: {e}")
                return False

            telegram_config = self.notifier.config
            has_telegram = any(telegram_config.values())
            if has_telegram:
                self.logger.info("Configuração Telegram detectada")
            else:
                self.logger.warning("Configuração Telegram não encontrada")

            cache_info = self.cache_service.get_cache_info()
            self.logger.info(
                f"Cache: {'existe' if cache_info['exists'] else 'não existe'}"
            )

            method = Config.get_extraction_method()
            self.logger.info(f"Método de extração: {method}")

            self.logger.info("Teste de configuração concluído")
            return True
        except Exception as e:
            self.logger.error(f"Erro no teste de configuração: {e}")
            return False


def main() -> None:
    """Ponto de entrada principal da aplicação."""
    debug_mode = "--debug" in sys.argv or "-d" in sys.argv
    test_mode = "--test" in sys.argv or "-t" in sys.argv

    scraper = SIGAAScraper(debug_mode=debug_mode)
    logger = get_logger("main")

    try:
        if test_mode:
            logger.info("Executando em modo de teste")
            if scraper.test_configuration():
                print("Configuração válida!")

                if scraper.notifier.config.get("bot_token"):
                    import os

                    is_github_actions = (
                        os.getenv("GITHUB_ACTIONS", "false").lower() == "true"
                    )

                    if is_github_actions:
                        logger.info(
                            "Validando configuração Telegram (GitHub Actions)..."
                        )
                    else:
                        logger.info("Testando notificação...")

                    if scraper.notifier.test_notification():
                        if is_github_actions:
                            print("Configuração Telegram validada!")
                        else:
                            print("Notificação teste enviada!")
                    else:
                        print("Falha no teste de notificação")
            else:
                print("Configuração inválida!")
                sys.exit(1)
            return

        # Execução normal
        changes = scraper.run()

        print("\n" + "=" * 60)
        print("RESULTADO DO SCRAPING")
        print("=" * 60)

        if changes:
            print(f"{len(changes)} mudança(s) detectada(s):")
            for i, change in enumerate(changes, 1):
                print(f"   {i}. {change}")

            import os

            is_github_actions = os.getenv("GITHUB_ACTIONS", "false").lower() == "true"
            enable_github_notifications = (
                os.getenv("ENABLE_GITHUB_NOTIFICATIONS", "false").lower() == "true"
            )

            if not is_github_actions or enable_github_notifications:
                logger.info("Enviando notificações...")
                if scraper.notifier.notify_changes(changes):
                    print("Notificações enviadas!")
                else:
                    print("Falha no envio de notificações")
            else:
                if is_github_actions and not enable_github_notifications:
                    logger.info(
                        "Notificações de mudanças desabilitadas no GitHub Actions"
                    )
                    print(
                        "Mudanças detectadas (notificações desabilitadas no GitHub Actions)"
                    )
                    print("Para habilitar, defina ENABLE_GITHUB_NOTIFICATIONS=true")
        else:
            print("Nenhuma mudança detectada nas notas.")

        print("=" * 60)
        print("Processo finalizado com sucesso!")

    except Exception as e:
        logger.error(f"Erro crítico da aplicação: {e}", exc_info=True)
        print(f"\nErro: {e}")
        print("Verifique o arquivo de log para mais detalhes:")
        print(f"   {Config.LOG_FILENAME}")

        try:
            scraper.notifier.notify_error(str(e))
        except Exception:
            pass

        sys.exit(1)


if __name__ == "__main__":
    main()
