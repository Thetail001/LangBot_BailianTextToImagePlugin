from http import HTTPStatus
from urllib.parse import urlparse, unquote
from pathlib import PurePosixPath
import requests
import asyncio
import os
import re
from dashscope import ImageSynthesis
from pkg.plugin.context import register, handler, llm_func, BasePlugin, APIHost, EventContext
from pkg.plugin.events import *  # 导入事件类
from plugins.LangBot_BailianTextToImagePlugin.config import Config
import pkg.platform.types as platform_types  # 导入 platform_types

# 注册插件
@register(name="LangBot_BailianTextToImagePlugin", description="调用阿里云百炼平台文生图API生成图片。", version="1.0", author="Thetail")
class TextToImage(BasePlugin):

    # 插件加载时触发
    def __init__(self, host: APIHost):
        super().__init__(host)
        model = Config.model
        os.environ["DASHSCOPE_API_KEY"] = Config.DASHSCOPE_API_KEY

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
                if re.search(r"[!！]ig", message.text):  # 检测是否包含 "!ig" 或 "！ig"
                    prompt = re.split(r"[!！]ig", message.text, 1)[-1].strip()  # 按 "!ig" 或 "！ig" 分割，并获取后面的部分
                    await self.process_command(ctx, prompt)
                    break

    async def process_command(self, ctx: EventContext, input_prompt: str):
        try:
            # 第一步：发起异步请求，获取任务 ID
            rsp = ImageSynthesis.async_call(model=model,
                                            prompt=input_prompt,
                                            size='1024*1024')

            if rsp.status_code != HTTPStatus.OK:
                self.ap.logger.error(f"Failed to start task: {rsp.code}, message: {rsp.message}")
                return

            # 第二步：轮询等待任务完成
            while True:
                await asyncio.sleep(2)  # 等待一段时间后再查询状态，避免频繁请求服务器

                status_rsp = ImageSynthesis.fetch(rsp)
                if status_rsp.status_code != HTTPStatus.OK:
                    self.ap.logger.error(f"Failed to fetch task status: {status_rsp.code}, message: {status_rsp.message}")
                    return
                
                if status_rsp.output.task_status == 'SUCCESS':
                    break   # 图片生成成功，跳出循环
                
                elif status_rsp.output.task_status in ['FAILED', 'ERROR']:
                    self.ap.logger.error(f"Task failed with status: {status_rsp.output.task_status}")
                    return

            # 第三步：获取最终结果
            final_rsp = ImageSynthesis.wait(rsp)

            if final_rsp.status_code == HTTPStatus.OK:
                result = final_rsp.output.results[0]
                url = result.url

                message_parts = [platform_types.Image(url=url)]
                ctx.add_return('reply', message_parts)
                ctx.prevent_default()
                ctx.prevent_postorder()
            
            else:
                self.ap.logger.error(f'Failed to retrieve image: {final_rsp.code}, message: {final_rsp.message}')

        except Exception as e:
            self.ap.logger.error(f"生成图片异常: {e}")

    # 插件卸载时触发
    def __del__(self):
        pass
