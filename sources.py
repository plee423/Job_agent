from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from typing import Protocol
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from matcher import SearchProfile, score_posting


@dataclass
class JobPosting:
    source: str
    title: str
    company: str
    location: str
    url: str
    published_at: str
    snippet: str
    score: float


class JobSource(Protocol):
    name: str

    def search(self, profile: SearchProfile, min_score: float = 0.15) -> list[JobPosting]:
        ...


class RemoteOkSource:
    name = "remoteok"

    def search(self, profile: SearchProfile, min_score: float = 0.15) -> list[JobPosting]:
        req = Request("https://remoteok.com/api", headers={"User-Agent": "job-agent/1.0"})
        with urlopen(req, timeout=20) as resp:
            raw = json.loads(resp.read().decode("utf-8"))

        postings: list[JobPosting] = []
        for item in raw:
            if not isinstance(item, dict) or "position" not in item:
                continue
            title = item.get("position", "")
            description = item.get("description", "") or ""
            score = score_posting(title, description, profile)
            if score < min_score:
                continue
            postings.append(
                JobPosting(
                    source=self.name,
                    title=title,
                    company=item.get("company", ""),
                    location=item.get("location", "remote") or "remote",
                    url=item.get("url", ""),
                    published_at=item.get("date", "") or datetime.utcnow().isoformat(),
                    snippet=(description[:300] + "...") if len(description) > 300 else description,
                    score=score,
                )
            )
        return postings


class WeWorkRemotelySource:
    name = "weworkremotely"

    def search(self, profile: SearchProfile, min_score: float = 0.15) -> list[JobPosting]:
        query = " ".join(profile.keywords[:5]).strip() or "software"
        url = f"https://weworkremotely.com/remote-jobs.rss?{urlencode({'term': query})}"
        req = Request(url, headers={"User-Agent": "job-agent/1.0"})
        with urlopen(req, timeout=20) as resp:
            xml_data = resp.read().decode("utf-8", errors="ignore")

        root = ET.fromstring(xml_data)
        postings: list[JobPosting] = []
        for item in root.findall("./channel/item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            description = (item.findtext("description") or "").strip()
            pub_date = (item.findtext("pubDate") or "").strip()
            score = score_posting(title, description, profile)
            if score < min_score:
                continue
            postings.append(
                JobPosting(
                    source=self.name,
                    title=title,
                    company="",
                    location="remote",
                    url=link,
                    published_at=pub_date,
                    snippet=(description[:300] + "...") if len(description) > 300 else description,
                    score=score,
                )
            )
        return postings


def default_sources() -> list[JobSource]:
    return [RemoteOkSource(), WeWorkRemotelySource()]
