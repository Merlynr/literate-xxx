import json
import os
import sys
import traceback
from http import HTTPStatus

import dashscope
import requests
from dashscope.aigc.image_generation import ImageGeneration
from dashscope.api_entities.dashscope_response import Message

# 与 tywx-demo.py 保持一致（北京地域；新加坡请改为 dashscope-intl 文档中的地址）
dashscope.base_http_api_url = "https://dashscope.aliyuncs.com/api/v1"

# 阿里云百炼 / DashScope
#API_KEY = os.environ.get("DASHSCOPE_API_KEY", "").strip()
API_KEY = "sk-a431b8698b9d4ab0825fdea07c82de8e"


def _script_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def _first_image_url_from_generation(rsp) -> str | None:
    """从 ImageGeneration 响应中取出第一张结果图 URL。"""
    if rsp.status_code != HTTPStatus.OK or not rsp.output:
        return None
    choices = getattr(rsp.output, "choices", None) or rsp.output.get("choices")
    if not choices:
        return None
    msg = choices[0].message if hasattr(choices[0], "message") else choices[0].get("message")
    if not msg:
        return None
    content = msg.content if hasattr(msg, "content") else msg.get("content")
    if isinstance(content, str):
        return None
    if not isinstance(content, list):
        return None
    for part in content:
        if isinstance(part, dict) and part.get("image"):
            return part["image"]
    return None


def build_wan_prompt_from_vs(product_path: str, style_path: str) -> tuple[str, dict]:
    """
    调用 vs.py 中的视觉解析（主体 + 参考海报风格），自动拼装通义万相中文指令。
    返回 (prompt_text, debug_dict)。
    """
    from vs import analyze_poster_style, analyze_product_subject

    print("正在解析商品主体 (vs.analyze_product_subject)...")
    subject = analyze_product_subject(product_path)
    print("正在解析参考海报风格 (vs.analyze_poster_style)...")
    style = analyze_poster_style(style_path)

    subj_json = json.dumps(subject, ensure_ascii=False, indent=2)
    style_json = json.dumps(style, ensure_ascii=False, indent=2)

    prompt = f"""
你正在使用「图1 + 图2」进行电商主图重绘与版式迁移。

【图1】待优化的商品实拍（必须保留真实产品结构、瓶型与标签可读性，不得虚构批号或医疗功效文案）。
【图2】成品海报参考（仅迁移光影、色调、装饰语言与整体氛围，不要把图2里的其他商品品牌当成图1）。

—— 机器解析 · 商品主体（须忠实执行 must_preserve）——
{subj_json}

—— 机器解析 · 参考图风格（用于背景、光效与装饰）——
{style_json}

—— 生成要求（中文执行）——
1. 以图1瓶身为唯一视觉中心，棚拍级布光；修正 defects_to_fix 中提到的实拍瑕疵（去杂乱背景、水印、脏光等）。
2. 背景与整体 vibe / lighting / composition 对齐上述 style 字段；可适当加入 props 中类似的点缀元素（成分球、微粒、草本图形等），但不要遮挡主标签关键信息。
3. 色彩可呼应 style.background 与 subject.palette；保留标签上的英文/中文信息结构与配色层级，不要胡乱改写药品名称。
4. 画质：商业电商主图，细腻材质、适度景深、干净高光；竖版海报构图。
5. 禁止：夸大医疗承诺、与图1不符的虚假成分说明、把参考图里的竞品 LOGO 贴到图1产品上。
""".strip()

    debug = {"subject": subject, "style": style}
    return prompt, debug


def _fallback_prompt() -> str:
    return """
图1为待优化的商品实物照片，图2为版式与视觉风格参考。
请生成专业电商主图：参考图2的浅蓝白渐变、科技感底纹与光效，
将图1中的产品作为唯一主体，去除杂乱背景，棚拍级布光与清晰标签，
整体干净、大健康质感，竖版海报构图；保留标签可读性，不虚构批号或功效。
""".strip()


def generate_optimized_poster(use_vs_prompt: bool = True):
    base = _script_dir()
    product_path = os.path.join(base, "shiwu.jpg")
    style_path = os.path.join(base, "demo3.jpg")

    if not API_KEY:
        print("❌ 未配置 DASHSCOPE_API_KEY，或在脚本中取消注释并填写 API_KEY。")
        sys.exit(1)

    prompt = _fallback_prompt()
    if use_vs_prompt:
        try:
            prompt, dbg = build_wan_prompt_from_vs(product_path, style_path)
            out_debug = os.path.join(base, "tywx_prompt_debug.json")
            with open(out_debug, "w", encoding="utf-8") as f:
                json.dump(dbg, f, ensure_ascii=False, indent=2)
            print(f"已根据 vs 解析自动生成 prompt，解析快照: {out_debug}")
        except Exception as e:
            print(f"⚠️ vs 解析失败，改用内置 fallback prompt。原因: {e}")
            traceback.print_exc()

    print("正在连接阿里云通义万相 API (wan2.7-image，ImageGeneration 多图编辑)...")

    message = Message(
        role="user",
        content=[
            {"text": prompt},
            {"image": product_path},
            {"image": style_path},
        ],
    )

    try:
        rsp = ImageGeneration.call(
            model="wan2.7-image",
            api_key=API_KEY,
            messages=[message],
            n=1,
            size="2K",
        )

        if rsp.status_code == HTTPStatus.OK:
            image_url = _first_image_url_from_generation(rsp)
            if not image_url:
                print("✅ 任务成功但未解析到图片 URL，完整响应：")
                print(rsp)
                return
            print(f"✅ 生成成功，下载链接: {image_url}")
            download_image(image_url, os.path.join(base, "final_product_poster.jpg"))
        else:
            print(f"❌ 任务失败: HTTP {rsp.status_code}")
            print(f"错误码: {getattr(rsp, 'code', '')}")
            print(f"错误信息: {getattr(rsp, 'message', '')}")

    except Exception as e:
        print(f"❌ 运行异常: {e}")


def download_image(url, save_path):
    print(f"正在保存图片至 {save_path} ...")
    response = requests.get(url, timeout=120)
    if response.status_code == 200:
        with open(save_path, "wb") as f:
            f.write(response.content)
        print("全部完成。")
    else:
        print("图片下载失败，可复制上方链接到浏览器下载。")


if __name__ == "__main__":
    base = _script_dir()
    if not os.path.isfile(os.path.join(base, "shiwu.jpg")):
        print("⚠️ 未找到 shiwu.jpg，请放在脚本同目录下。")
    elif not os.path.isfile(os.path.join(base, "demo3.jpg")):
        print("⚠️ 未找到 demo3.jpg（风格参考图），请放在脚本同目录下。")
    else:
        # 若无需调用 mimo 解析，可改为 generate_optimized_poster(use_vs_prompt=False)
        generate_optimized_poster(use_vs_prompt=True)
