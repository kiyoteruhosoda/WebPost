from dotenv import load_dotenv

from application.handlers.scrape_handler import ScrapeStepHandler
from application.services.form_composer import FormComposer
from domain.steps.scrape import ScrapeStep
from infrastructure.logging.console_logger import ConsoleLogger
load_dotenv()

from infrastructure.logging.log_setup import setup_console_logging
setup_console_logging(level="DEBUG")


from application.executor.handler_registry import HandlerRegistry
from application.executor.step_executor import StepExecutor
from application.handlers.http_handler import HttpStepHandler
from application.services.template_renderer import TemplateRenderer
from application.services.execution_deps import ExecutionDeps
from application.ports.requests_client import RequestsSessionHttpClient


from infrastructure.secrets.env_secret_provider import EnvSecretProvider
from infrastructure.url.base_url_resolver import BaseUrlResolver

from domain.run import RunContext
from domain.steps.http import HttpStep, HttpRequestSpec


def main():
    http_client = RequestsSessionHttpClient()

    renderer = TemplateRenderer()
    http_handler = HttpStepHandler(http_client=http_client, renderer=renderer)
    scrape_handler = ScrapeStepHandler()

    registry = HandlerRegistry([http_handler, scrape_handler])
    executor = StepExecutor(registry)
    
    deps = ExecutionDeps(
        secret_provider=EnvSecretProvider(),
        url_resolver=BaseUrlResolver(base_url="https://fun-navi.net"),
        logger=ConsoleLogger(),   # ← levelは渡さない
    )

    steps = [
        HttpStep(
            id="login_get",
            name="login_get",
            request=HttpRequestSpec(method="GET", url="/FRPC010G_LoginAction.do"),
        ),
        ScrapeStep(
            id="scrape_login_hidden",
            name="scrape_login_hidden",
            command="hidden_inputs",
            save_as="login_hidden",
        ),
        HttpStep(
            id="login_post",
            name="login_post",
            request=HttpRequestSpec(
                method="POST",
                url="/FRPC010G_LoginAction.do",
                merge_from_vars="login_hidden",
                form_list=[
                    ("screenID", "FRPC010G"),
                    ("referrer", ""),
                    ("fulltimeID", "${secrets.fulltimeID}"),
                    ("password", "${secrets.password}"),
                    ("loginBTN", "ログイン"),
                ],
            ),
        ),
    ]


    ctx = RunContext(vars={})

    result = executor.execute(steps, ctx, deps)
    print(result)
    print("last.status:", ctx.last.status if ctx.last else None)
    print("last.url:", ctx.last.url if ctx.last else None)

    # 失敗理由確認（先頭だけ）
    if ctx.last:
        print("last.text.head:", ctx.last.text[:500])


if __name__ == "__main__":
    main()
