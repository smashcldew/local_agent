# skills/manager.py
#
# 技能載入器。格式參考 NousResearch/hermes-agent (MIT) 的 skills/ 與 agentskills.io:
# 每個技能一個資料夾,內含 SKILL.md(YAML frontmatter + 內文)。
# 為維持本地零依賴,這裡自寫極簡 frontmatter 解析,只取 name / description。
# 參見 LICENSES/hermes-agent-MIT.txt
import os

try:
    from constants import get_maverick_home
except Exception:  # constants 不可用時仍可運作(只掃 repo 內建技能)
    get_maverick_home = None


def _parse_frontmatter(text: str):
    """解析 '---\\n key: value ... \\n---\\n 內文'。回傳 (meta: dict, body: str)。"""
    meta, body = {}, text.strip()
    if text.startswith("---"):
        lines = text.splitlines()
        end = None
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end = i
                break
        if end is not None:
            for ln in lines[1:end]:
                if ":" in ln:
                    k, v = ln.split(":", 1)
                    meta[k.strip()] = v.strip()
            body = "\n".join(lines[end + 1:]).strip()
    return meta, body


class SkillManager:
    """掃描技能資料夾,提供列表、取用與 catalog 文字(供注入 prompt)。"""

    def __init__(self, skills_dirs=None):
        if skills_dirs is None:
            skills_dirs = [os.path.dirname(os.path.abspath(__file__))]  # repo 內建技能
            if get_maverick_home:
                try:
                    skills_dirs.append(os.path.join(str(get_maverick_home()), "skills"))  # 使用者技能
                except Exception:
                    pass
        self.skills_dirs = [d for d in skills_dirs if d]
        self._cache = None

    def _scan(self):
        skills = {}
        for base in self.skills_dirs:
            if not os.path.isdir(base):
                continue
            for entry in sorted(os.listdir(base)):
                sub = os.path.join(base, entry)
                md = os.path.join(sub, "SKILL.md")
                if os.path.isdir(sub) and os.path.isfile(md):
                    try:
                        text = open(md, encoding="utf-8").read()
                    except Exception:
                        continue
                    meta, body = _parse_frontmatter(text)
                    name = meta.get("name", entry)
                    skills[name] = {
                        "name": name,
                        "description": meta.get("description", ""),
                        "path": md,
                        "body": body,
                    }
        return skills

    def _ensure(self):
        if self._cache is None:
            self._cache = self._scan()
        return self._cache

    def reload(self):
        self._cache = self._scan()
        return self._cache

    def list_skills(self):
        return [{"name": s["name"], "description": s["description"]}
                for s in self._ensure().values()]

    def get_skill(self, name: str):
        s = self._ensure().get(name)
        return s["body"] if s else None

    def render_catalog(self) -> str:
        """產生一段「可用技能清單」文字,可注入系統 prompt。無技能時回空字串。"""
        items = self.list_skills()
        if not items:
            return ""
        lines = ["【可用技能 Skills】(需要時呼叫 skill_view 取得完整步驟)"]
        for s in items:
            lines.append(f"- {s['name']}: {s['description']}")
        return "\n".join(lines)
