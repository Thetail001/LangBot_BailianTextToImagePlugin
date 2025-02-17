from http import HTTPStatus
from urllib.parse import urlparse, unquote
from pathlib import PurePosixPath
import requests
import asyncio
import os
from dashscope import ImageSynthesis
from pkg.plugin.context import register, handler, llm_func, BasePlugin, APIHost, EventContext
from pkg.plugin.events import *  # 导入事件类
from plugins.BailianTextToImagePlugin.config import Config
from pkg.plugin.types import platform_types  # 导入 platform_types


model = Config.model
os.environ[DASHSCOPE_API_KEY] = Config.DASHSCOPE_API_KEY

# 注册插件
@register(name="LangBot_BailianTextToImagePlugin", description="调用阿里云百炼平台文生图API生成图片。", version="1.0", author="Thetail")
class TextToImage(BasePlugin):

    # 插件加载时触发
    def __init__(self, host: APIHost):
        super().__init__(host)
        pass

    # 异步初始化
    async def initialize(self):
        pass

    # 当收到消息时触发
    @handler(PersonNormalMessageReceived)
    @handler(GroupNormalMessageReceived)
    async def on_message(self, ctx: EventContext):
        await self.process_message(ctx)

    async def process_message(self, ctx: EventContext):
        """处理收到的消息"""
        message_chain = ctx.event.query.message_chain
        for message in message_chain:
            if isinstance(message, platform_types.Plain):
                if "/ig" in message.text:  # 检测是否包含 "/ig"
                    prompt = message.text.replace("/ig", "", 1).strip()  # 去掉 "/ig"，并去除前后空格
                    await self.process_command(ctx, prompt)
                    break

    async def process_command(self, ctx: EventContext, input_prompt: str):
         try:
            rsp = await ImageSynthesis.async_call(model=model,  # 修正异步调用方式
                                                  prompt=input_prompt,
                                                  size='1024*1024')
            if rsp.status_code == HTTPStatus.OK:
                output = rsp.output
                if output.task_status == 'SUCCESSED':
                    result = output.results[0]
                    url = result.url
                    message_parts = [
                        platform_types.Image(url=url) 
                    ]
                    ctx.add_return('reply', message_parts)
                    ctx.prevent_default()
                    ctx.prevent_postorder()
                else:
                    self.ap.logger.error(f"Failed, task_status: {output.task_status}")
            else:
                self.ap.logger.error('Failed, status_code: %s, code: %s, message: %s' %
                        (rsp.status_code, rsp.code, rsp.message))
         except Exception as e:
            self.host.logger.error(f"生成图片异常: {e}")

    # 插件卸载时触发
    def __del__(self):
        pass
