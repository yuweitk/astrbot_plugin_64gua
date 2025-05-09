import os
import random
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import astrbot.api.message_components as Comp

PLUGIN_DIR = os.path.dirname(__file__)
IMAGE_DIR = os.path.join(PLUGIN_DIR, "64gua")  # 卦象图片存储路径

@register("astrbot_plugin_64gua", "IamAGod", "周易金钱卦插件", "1.0.0")
class GuaPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.gua_images = []  # 存储卦象图片文件名列表
        self.total_gua = 64   # 六十四卦总数

    async def initialize(self):
        """插件初始化时加载卦象图片"""
        try:
            if not os.path.exists(IMAGE_DIR):
                logger.error(f"卦象文件夹 {IMAGE_DIR} 不存在")
                return
            
            # 加载所有符合命名规范的图片文件[6](@ref)
            self.gua_images = [
                f for f in os.listdir(IMAGE_DIR)
                if f.endswith('.jpg') and f.startswith('64gua_')
            ]
            
            # 验证图片数量[7](@ref)
            if len(self.gua_images) != self.total_gua:
                logger.warning(f"卦象图片数量异常，期望64张，实际找到{len(self.gua_images)}张")
            
            logger.info(f"成功加载 {len(self.gua_images)} 张卦象图片")

        except Exception as e:
            logger.error(f"初始化失败: {str(e)}")
            self.gua_images = []

    @filter.command("金钱卦")
    async def send_random_gua(self, event: AstrMessageEvent):
        """处理金钱卦指令"""
        if not self.gua_images:
            yield event.plain_result("未找到卦象图片，请联系管理员检查插件配置")
            return

        try:
            # 随机选择卦象图片[6](@ref)
            selected_image = random.choice(self.gua_images)
            image_path = os.path.join(IMAGE_DIR, selected_image)
            
            # 构建消息链[2](@ref)
            chain = [
                Comp.Plain("🔮 周易金钱卦推算结果："),
                Comp.Image.fromFileSystem(image_path),
                Comp.Plain("\n『卦象已显，吉凶自辨』")
            ]
            
            yield event.chain_result(chain)
            
            # 记录操作日志[5](@ref)
            logger.info(f"用户 {event.get_sender_id()} 获取卦象 {selected_image}")

        except FileNotFoundError:
            error_msg = f"卦象图片 {selected_image} 不存在"
            logger.error(error_msg)
            yield event.plain_result("卦象显化失败，请稍后再试")
        except Exception as e:
            logger.error(f"未知错误: {str(e)}")
            yield event.plain_result("卦象推算异常，请联系管理员")

    async def terminate(self):
        """插件卸载时清理资源"""
        self.gua_images.clear()
        logger.info("周易金钱卦插件已卸载")
