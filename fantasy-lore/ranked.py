"""Alternating fantasy podcast listening order. No private setting data or MP3 copies."""
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import math
import re

def normalize(value):
    return re.sub(r"[^a-z0-9 ]+", " ", (value or "").casefold()).split()

def sim(a,b):
    ta=set(normalize(a)); tb=set(normalize(b))
    return len(ta & tb) / max(1,len(ta))

def story_chapters(source, episodes, resolve_length):
    """Resolve declared serial entry sequence from publisher RSS, stop at first gap."""
    found=[]; notices=[]
    seen=set()
    for fragment in source["story_playlist"]:
        matches=[x for x in episodes if sim(fragment, x.findtext("title") or "") >= .95]
        if len(matches)!=1:
            notices.append(f"Cannot uniquely match chapter: {fragment} ({len(matches)} results)")
            break
        episode=matches[0]
        audio=episode.find("enclosure")
        url=audio.get("url","") if audio is not None else ""
        if not url.startswith("https://") or url in seen:
            notices.append(f"Invalid or repeated audio for chapter: {fragment}")
            break
        length=resolve_length(audio)
        if length<1:
            notices.append(f"No nonzero publisher enclosure length for: {fragment}")
            break
        seen.add(url)
        try:date=parsedate_to_datetime(episode.findtext("pubDate") or "").timestamp()
        except Exception:date=0
        found.append(dict(source=source,item=episode,score=0.0,published=date,
                          themes=["gm"],length=length,role="story",chapter=len(found)+1))
    return found, {"story_gaps":notices}

def bayes(source,ranking):
    r=source.get("rating_us",{})
    n=r.get("count",0); stars=r.get("stars",ranking["shrinkage_prior"])
    return (n*stars+ranking["shrinkage_weight"]*ranking["shrinkage_prior"])/(n+ranking["shrinkage_weight"])

def relevance(item,source,config):
    title=(item.findtext("title") or "").casefold()
    description=(item.findtext("description") or "")[:1400].casefold()
    terms=("monster","creature","ecology","gods","deity","drow","underdark",
           "fey","dragon","aberration","ritual","culture","society","politic",
           "undead","horror","village","forest","history","mystery","spirit",
           "magic","religion","settlement","npc","planar","beholder","witch")
    title_hits=sum(x in title for x in terms)
    desc_hits=sum(x in description for x in terms)
    spotlight=sum(x.casefold() in title for x in config["spotlight_terms"])
    return min(1.0,.18+.11*title_hits+.025*desc_hits+.07*spotlight)

def creative(item,role):
    description=((item.findtext("title") or "")+" "+(item.findtext("description") or "")[:1300]).casefold()
    keywords=["talk","voices","relationship","friend","society","culture","village",
              "god","faith","ritual","travel","character","conflict","court",
              "queen","king","history","people","community","horror","encounter",
              "mystery","dialogue","story","faction","folk"]
    value=min(1.0,.24+.08*sum(x in description for x in keywords))
    return max(value,.82) if role=="story" else value

def score(entry,config):
    rating=min(1,max(0,(bayes(entry["source"],config["ranking"])-3.5)/1.5))
    topic=relevance(entry["item"],entry["source"],config)
    storytelling=creative(entry["item"],entry["role"])
    weights=config["ranking"]
    entry["score"]=round(100*(weights["rating_weight"]*rating+
                               weights["episode_relevance_weight"]*topic+
                               weights["creative_utility_weight"]*storytelling+
                               weights["diversity_weight"]*.70),2)
    return entry["score"]

def rank(entries, config):
    lore=[x for x in entries if x["role"]=="lore"]
    chapters=[x for x in entries if x["role"]=="story"]
    for x in entries:score(x,config)
    arcs={}
    for e in chapters:
        arcs.setdefault(e["source"]["id"],[]).append(e)
    for seq in arcs.values():seq.sort(key=lambda x:x["chapter"])
    # One narrative at a time, chapters never reordered.
    arc_keys=sorted(arcs,key=lambda k:(-bayes(arcs[k][0]["source"],config["ranking"]),k))
    story=[]
    for k in arc_keys:story+=arcs[k][:config["ranking"]["max_story_per_show"]]
    limit=min(len(story),len(lore),config["ranking"]["max_pairs"])
    if len(arcs)<2 or limit<6:
        raise RuntimeError(f"Only {len(arcs)} verified story series and {limit} possible pairs")
    used=set();per_show={};taken=[];seen_themes={}
    for target in story[:limit]:
        target_text=(" ".join([target["item"].findtext("title") or "",
                                target["source"].get("note",""),
                                (target["item"].findtext("description") or "")[:700]])).casefold()
        options=[]
        for e in lore:
            uri=e["item"].find("enclosure").get("url")
            show=e["source"]["id"]
            if uri in used or per_show.get(show,0)>=config["ranking"]["max_lore_per_show"]:
                continue
            title=(e["item"].findtext("title") or "").casefold()
            common=sum(term in title and term in target_text for term in
                       ("dragon","fey","faith","god","ritual","horror","monster",
                        "forest","cult","undead","magic","drow","politic","elf","witch"))
            diversity=3*max(0,3-per_show.get(show,0))
            category=2*sum(seen_themes.get(t,0)<3 for t in e["themes"])
            options.append((e["score"]+min(10,2.3*common)+diversity+category,e))
        if not options:break
        best=max(options,key=lambda a:(a[0],a[1]["source"]["id"]))[1]
        taken.append(best)
        used.add(best["item"].find("enclosure").get("url"))
        ident=best["source"]["id"];per_show[ident]=per_show.get(ident,0)+1
        for theme in best["themes"]:seen_themes[theme]=seen_themes.get(theme,0)+1
    paired=[]
    for a,b in zip(taken,story):paired.extend([a,b])
    if len(paired)<12:raise RuntimeError("Ranked mix is too thin")
    return paired

def manifest(entries):
    output=[]
    for rank,e in enumerate(entries,1):
        item=e["item"];source=e["source"];rating=source.get("rating_us",{})
        output.append({
            "rank":rank,"role":e["role"].upper(),"title":item.findtext("title") or "",
            "show":source["title"],"show_rating_us":rating.get("stars"),
            "show_rating_count_us":rating.get("count"),
            "rating_reference":rating.get("url"),"heuristic_score":e["score"],
            "serial_chapter":e.get("chapter"),"themes":e["themes"],
            "original_pubdate":item.findtext("pubDate") or "",
            "publisher_url":item.findtext("link") or source["publisher_site"],
            "creative_use":source.get("note","")})
    return output

def markdown(entries):
    lines=["# Ranked Fantasy Lore + Story Podcast Episodes","","**Play order alternates LORE → STORY.** Serialized stories keep their chapter order. Podcast app ordering dates are synthetic; each item's original date is retained separately.","",
           "**Ratings are SHOW-LEVEL Apple US ratings, never fabricated episode ratings.** Scores (/100) are editorial algorithm estimates based on topic usefulness, story/NPC craft, smoothed show ratings and source variety.","",
           "| # | Kind | Verified source episode | Apple US show rating | Editorial score | Why listen |",
           "|---:|---|---|---|---:|---|"]
    for row in manifest(entries):
        title=row["title"].replace("|","-");name=row["show"].replace("|","-")
        why=row["creative_use"].replace("|","-")
        r=f'{row["show_rating_us"]}/5 ({row["show_rating_count_us"]} ratings)' if row["show_rating_us"] else "Not recorded"
        lines.append(f'| {row["rank"]} | {row["role"]} | [{title}]({row["publisher_url"]}) — {name} | {r} | {row["heuristic_score"]:.1f} | {why} |')
    lines+=["","## Methodology",
            "Weighted: 52% topical episode relevance, 22% usefulness for NPCs and narrative craft, 16% Bayesian-smoothed show rating (4.5 prior with 250 votes), 10% diversity. Source novelty and theme pair matching are also applied when choosing each lore/story pair.",
            "Serial selections are verified against original publisher RSS and stopped at the first missing chapter. This isn't a ranking of most-liked individual episodes.",
            "Publisher-hosted recordings and original episode attribution are retained. No original recordings are mirrored.",
            ""]
    return "\n".join(lines)
