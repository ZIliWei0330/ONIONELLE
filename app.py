from flask import Flask, request, Response, send_file
import time
import os
import openai

openai.api_key = os.environ.get('OPENAI_API_KEY')

app = Flask(__name__)

def get_onion_layers(text, mode='inflate'):
    if mode == 'inflate':
        prompt = (
            "请将以下文本分为九层递进，每一层都像身份错乱、假象与真相交织的当代艺术家，"
            "用极度装腔、学术、抽象、诗意、隐喻、假照片、钓鱼、剥洋葱、被钓等主题不断递进，"
            "让内容越来越玄乎、装逼、复杂，结尾极度自嘲或荒谬。"
            "每层用中文序号（一、二…），不可用阿拉伯数字，每层只写一遍序号和内容，禁止英文、禁止Markdown。"
            f"文本内容：“{text}”"
        )
    else:
        prompt = (
            "请将以下内容分为九层递进，每层用最通俗、土味、网络、吐槽、讽刺的风格翻译，"
            "像市井大爷调侃艺术家、假照、钓鱼、剥洋葱这些行为，每层递减，结尾可自嘲、反高潮、网络流行语。"
            "每层用中文序号（一、二…），每层只写一遍序号和内容，禁止英文、禁止Markdown。"
            f"文本内容：“{text}”"
        )

    try:
        import re
        print("[DEBUG] 即将请求 OpenAI API")
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1800,
            temperature=0.8,
            stream=True
        )
        buffer = ""
        for chunk in response:
            delta = chunk['choices'][0]['delta']
            if 'content' in delta:
                buffer += delta['content']
                lines = re.split(r'[\r\n]+', buffer)
                buffer = lines[-1]
                for line in lines[:-1]:
                    line = line.strip()
                    if not line:
                        continue
                    if re.search(r"(我得理解|用户希望|我要先|需要注意|总结一下)", line):
                        continue
                    print(f"[DEBUG] yield line: {line}")
                    yield line.encode("utf-8")
        final_line = buffer.strip()
        if final_line and not re.search(r"(我得理解|用户希望|我要先|需要注意|总结一下)", final_line):
            print(f"[DEBUG] yield final line: {final_line}")
            yield final_line.encode("utf-8")
    except Exception as e:
        import traceback
        traceback.print_exc()
        fallback_text = [
            "装腔失败，艺术家流泪下班。",
            "这洋葱又臭又辣，剥了半天没剥出层次感。",
            "老板说了，剥洋葱要有耐心，可你们这操作真是离谱。",
            "再剥下去眼泪都流出来了，别说味道了，连形状都不对。",
            "其实这洋葱就是个洋葱，别想太多，吃了就完事儿。"
        ]
        for line in fallback_text:
            print(f"[DEBUG] fallback yield line: {line}")
            yield line.encode("utf-8")

@app.route('/')
def index():
    return send_file("index.html")

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    print("收到 /analyze 请求")
    try:
        mode = request.args.get('mode', 'inflate')
        if request.method == 'GET':
            text = request.args.get('text', 'Default test text')
        else:
            text = request.json.get('text', 'Default test text')
        print(f"收到文本：{text}，模式：{mode}")
        analysis_generator = get_onion_layers(text, mode=mode)
        print("开始分析并流式返回结果")
        def generate():
            print("[DEBUG] yield initial message: 正在剥开洋葱......")
            yield "data: 正在剥开洋葱......\n\n".encode("utf-8")
            time.sleep(5)
            print("[DEBUG] yield message: 洋葱已剥开！让我闻一下什么味道！")
            yield "data: 洋葱已剥开！让我闻一下什么味道！\n\n".encode("utf-8")
            time.sleep(3)
            for line in analysis_generator:
                decoded_line = line.decode("utf-8")
                print(f"[DEBUG] yield data: {decoded_line}")
                yield f"data: {decoded_line}\n\n".encode("utf-8")
                time.sleep(2)
        return Response(generate(), mimetype='text/event-stream')
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("OpenAI调用异常：", e)
        fallback_text = [
            "装腔失败，艺术家流泪下班。",
            "这洋葱又臭又辣，剥了半天没剥出层次感。",
            "老板说了，剥洋葱要有耐心，可你们这操作真是离谱。",
            "再剥下去眼泪都流出来了，别说味道了，连形状都不对。",
            "其实这洋葱就是个洋葱，别想太多，吃了就完事儿。"
        ]
        def fallback_generate():
            for line in fallback_text:
                print(f"[DEBUG] fallback yield line: {line}")
                yield f"data: {line}\n\n".encode("utf-8")
        error_msg = f"错误：{str(e)}"
        print("analyze 捕获异常：", error_msg)
        def error_generate():
            print(f"[DEBUG] error yield message: {error_msg}")
            yield f"data: {error_msg}\n\n".encode("utf-8")
            print("[DEBUG] error yield message: 洋葱剥不开，哭着也要吃完它。")
            yield "data: 洋葱剥不开，哭着也要吃完它。\n\n".encode("utf-8")
        return Response(fallback_generate(), mimetype='text/event-stream') if not error_msg else Response(error_generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))