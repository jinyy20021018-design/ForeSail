# Vibe 选手材料收集 Skill 使用说明

这份 Skill 会通过中文分轮问答，帮助选手整理参赛材料、检查缺失项，并生成组织结构一致的提交文件夹。它不会替选手编造用户证据、技术使用情况或测试结果。

## 一、使用前准备

- 一个支持 `SKILL.md` 格式的 Agent，推荐使用 Codex。
- Python 3。终端中运行 `python3 --version`；Windows 也可以运行 `python --version`。
- 解压后的 Skill 文件夹名称必须保持为 `vibe-submission-collector`。

## 二、安装方法

### 方法 A：安装到个人 Codex（推荐）

安装后，此 Skill 可以在你的不同项目和新任务中使用。

macOS 或 Linux：

```bash
mkdir -p ~/.codex/skills
unzip vibe-submission-collector.zip -d ~/.codex/skills
```

Windows PowerShell：

```powershell
New-Item -ItemType Directory -Force "$HOME\.codex\skills"
Expand-Archive -Path .\vibe-submission-collector.zip -DestinationPath "$HOME\.codex\skills" -Force
```

安装后的目录应为：

```text
~/.codex/skills/vibe-submission-collector/SKILL.md
```

### 方法 B：只安装到当前项目

在项目根目录创建 `.agents/skills/`，然后把解压后的整个文件夹放进去：

```text
<你的项目>/
└── .agents/
    └── skills/
        └── vibe-submission-collector/
            ├── SKILL.md
            ├── agents/
            ├── references/
            └── scripts/
```

安装完成后，请新建一个 Agent 任务或重新启动 Agent，使其重新发现 Skill。

## 三、开始收集材料

在新任务中输入：

```text
使用 $vibe-submission-collector 帮我收集 Vibe-a-thon 参赛资料，材料输出到桌面。
```

如果你的 Agent 不支持 `$技能名` 写法，可以输入：

```text
请使用“Vibe 选手材料收集”Skill，通过问答帮我整理参赛资料并生成提交文件夹。
```

Agent 每轮最多询问五个问题。你可以直接提供已有材料，也可以回答“暂不提供”。如果不理解某个字段，请询问“这个字段是什么意思”，Agent 会解释当前字段。

## 四、哪些信息必须提供

以下信息会影响组织方联系和证书制作，必须填写：

- 选手姓名，按照获奖证书展示方式填写；
- 手机号；
- 个人参赛或团队参赛；
- 团队参赛时，全部团队成员的证书姓名；
- 作品是否在比赛前已经存在；
- 比赛期间新增了哪些内容；
- 原创性确认；
- 同意评委访问和测试作品。

其他参赛信息不是提交门槛，但缺失可能影响对应评分。礼品收件人、电话和邮寄地址是可选信息。

## 五、Demo、视频和大文件

- 演示视频、安装包、源代码压缩包、数据集以及超过 10 MB 的文件，请提交可访问的在线播放或网盘链接。
- 提交前请使用无痕窗口检查链接，确保评审不需要再次申请权限。
- Demo 需要登录时，只提供专用临时测试账号，不要提供个人账号、生产账号、API Key 或真实用户数据。

## 六、确认与回传

Agent 生成材料包后，会先执行校验并列出缺失或未验证的信息。请检查内容，修改完成后明确回复“确认提交”。

确认后，请通过邮件将整理好的信息包发回给组织方：**gdghangzhou@163.com**。如果文件夹太大，可以先上传云网盘，然后发送链接。（请选手自行确保发送的链接可以公开访问）

材料包中的 `private/` 文件夹可能包含临时测试账号和礼品邮寄信息。不要把该文件夹放入公开网盘链接；请将其中的文件作为邮件附件，或使用单独的受控链接发给组织方。

## 七、常见问题

### Agent 找不到 Skill

确认目录中直接存在 `vibe-submission-collector/SKILL.md`，没有多套一层同名文件夹，然后新建任务或重启 Agent。

### 提示找不到 Python

安装 Python 3，并确认 `python3 --version` 或 `python --version` 至少有一个命令可以正常运行。

### 暂时没有用户证据或本地化测试怎么办

可以如实填写“暂未验证”或“暂不提供”。这不会阻止材料包生成，但会产生评分影响提示，评委可能无法在对应维度给出高分。

### 可以让 AI 优化文字吗

可以。Agent 会根据你的原始回答整理表达，但最终事实、链接和证据必须由你确认，不得让 AI 虚构。
