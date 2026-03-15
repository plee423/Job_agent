from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import os
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


class SerpApiSource:
    """Google Jobs via SerpApi — surfaces LinkedIn, Glassdoor, and other aggregated listings."""

    name = "serpapi"
    _BASE = "https://serpapi.com/search"

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or os.environ.get("SERPAPI_KEY", "")

    def search(self, profile: SearchProfile, min_score: float = 0.15) -> list[JobPosting]:
        if not self._api_key:
            raise RuntimeError("SERPAPI_KEY env var is not set — SerpApi source is disabled.")

        query = " ".join(profile.keywords[:8]).strip() or "software engineer"
        payload: dict = {
            "engine": "google_jobs",
            "q": query,
            "api_key": self._api_key,
            "chips": "date_posted:week",
            "num": "20",
        }
        if profile.location:
            payload["location"] = profile.location
        params = urlencode(payload)
        req = Request(f"{self._BASE}?{params}", headers={"User-Agent": "job-agent/1.0"})
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        postings: list[JobPosting] = []
        for item in data.get("jobs_results", []):
            title = item.get("title", "")
            company = item.get("company_name", "")
            location = item.get("location", "")
            description = item.get("description", "") or ""
            published_at = item.get("detected_extensions", {}).get("posted_at", "") or datetime.utcnow().isoformat()

            # Pick the best apply URL — prefer LinkedIn/Glassdoor direct links
            url = ""
            for link in item.get("related_links", []):
                href = link.get("link", "")
                if href:
                    url = href
                    break
            if not url:
                # Fall back to the SerpApi job detail page (still has the source link)
                url = item.get("job_id", "")
                if url:
                    url = f"https://www.google.com/search?q={urlencode({'ibp': 'htl;jobs', 'htivrt': 'jobs', 'htiq': query})}&sxsrf=&jbr=sep:0#htivrt=jobs&htiq={urlencode({'': query})[1:]}&fpstate=tldetail&htiltype=JOBS&htichips=job_family_1:job_category&htischips=job_family_1:job_category&sxsrf=&htidocid={url}"

            if not url:
                continue

            score = score_posting(title, description, profile)
            if score < min_score:
                continue

            postings.append(
                JobPosting(
                    source=self.name,
                    title=title,
                    company=company,
                    location=location,
                    url=url,
                    published_at=published_at,
                    snippet=(description[:300] + "...") if len(description) > 300 else description,
                    score=score,
                )
            )
        return postings


def default_sources() -> list[JobSource]:
    sources: list[JobSource] = [RemoteOkSource(), WeWorkRemotelySource()]
    if os.environ.get("SERPAPI_KEY"):
        sources.append(SerpApiSource())
    return sources
