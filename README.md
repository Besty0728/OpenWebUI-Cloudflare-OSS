<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=0,2,2,5,30&height=160&section=header&text=🌈%20你好啊，欢迎来到OpenWebUI-Cloudflare-OSS部署指南%20✨&fontSize=28&fontColor=fff&animation=twinkling&fontAlignY=40" />

# OpenWebUI-Cloudflare-OSS部署指南
最近在使用OpenWebUI接入CloudFlare的OSS模型时发现一些兼容问题，在社区寻找相同的解决方案时发现了一个Pipe可以解决这个问题，[社区方案](https://github.com/jrkropp/open-webui-developer-toolkit/tree/main/functions/pipes/openai_responses_manifold)  但是这个方案我发现在第二次对话后会出现一些细微的错误，解决起来太麻烦了，所以我决定自己写一个Pipe来解决这个问题，经过一番调试终于成功了，下面是具体的部署步骤

## 部署步骤

### 1. 在OpenWebUI ▸ 管理面板 ▸ 功能 中，单击从链接导入 。
 <img width="450" alt="image" src="https://github.com/user-attachments/assets/4a5a0355-e0af-4fb8-833e-7d3dfb7f10e3" />

### 2. 在弹出的对话框中，输入以下URL，然后单击导入按钮：
```bash
https://github.com/Besty0728/OpenWebUI-Cloudflare-OSS/blob/main/cloudflare_responses.py
```
### 3.⚠️ 重要提示，不要改动Pipe的Pipe ID，必须保持为 `cloudflare_responses`，否则无法正常工作。（除非你将我们的文件名称一并改动）
这个值目前是硬编码，必须完全匹配，未来版本或许可配置

### 4. 导入后，您应该会在功能列表中看到 `cloudflare_responses` 。
填入你的
- CloudFlare 账号ID
- CloudFlare API Key
- 模型名称（默认即可，因为我们项目就是为OSS两款参数设计的）