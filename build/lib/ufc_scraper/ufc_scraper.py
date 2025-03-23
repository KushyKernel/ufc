import requests as req
from lxml import html
import datetime as dt
import time
import random
from googlesearch import search
import logging

from .config import USER_AGENT, MAX_RETRIES, BASE_URL_UFC, BASE_URL_SHERDOG, BASE_URL_UFCSTATS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a global session for reusing connections.
session = req.Session()
DEFAULT_HEADERS = {"User-Agent": USER_AGENT}

def safe_xpath(context, query: str) -> str:
    result = context.xpath(query)
    return result[0].strip() if result else ""

def parse_sherdog_fighter(url: str) -> dict:
    try:
        response = session.get(url, headers=DEFAULT_HEADERS)
        response.raise_for_status()
    except req.RequestException as e:
        logger.error(f"Error fetching Sherdog URL {url}: {e}")
        raise

    xml = html.document_fromstring(response.content)
    wins_detailed = xml.xpath("//div[@class='wins']/div[@class='meter']/div[1]/text()")
    losses_detailed = xml.xpath("//div[@class='loses']/div[@class='meter']/div[1]/text()")
    bio_list = xml.xpath("//div[@class='fighter-info']")
    bio = bio_list[0] if bio_list else xml
    other_wins = wins_detailed[3] if len(wins_detailed) > 3 else '0'
    other_losses = losses_detailed[3] if len(losses_detailed) > 3 else '0'

    fighter = {
        'name': safe_xpath(xml, "//span[@class='fn']/text()"),
        'nickname': safe_xpath(bio, ".//span[@class='nickname']/em/text()"),
        'nationality': safe_xpath(bio, ".//strong[@itemprop='nationality']/text()"),
        'birthplace': safe_xpath(xml, "//span[@class='locality']/text()"),
        'birthdate': safe_xpath(xml, "//span[@itemprop='birthDate']/text()"),
        'age': safe_xpath(xml, "//span[@itemprop='birthDate']/preceding-sibling::b/text()"),
        'height': safe_xpath(xml, "//b[@itemprop='height']/text()"),
        'weight': safe_xpath(xml, "//b[@itemprop='weight']/text()"),
        'association': safe_xpath(xml, "//span[@itemprop='memberOf']/a/span/text()"),
        'weight_class': safe_xpath(xml, "//div[@class='association-class']/a/text()"),
        'wins': {
            'total': safe_xpath(xml, "//div[@class='winloses win']/span[2]/text()"),
            'ko/tko': wins_detailed[0] if len(wins_detailed) > 0 else "0",
            'submissions': wins_detailed[1] if len(wins_detailed) > 1 else "0",
            'decisions': wins_detailed[2] if len(wins_detailed) > 2 else "0",
            'others': other_wins
        },
        'losses': {
            'total': safe_xpath(xml, "//div[@class='winloses lose']/span[2]/text()"),
            'ko/tko': losses_detailed[0] if len(losses_detailed) > 0 else "0",
            'submissions': losses_detailed[1] if len(losses_detailed) > 1 else "0",
            'decisions': losses_detailed[2] if len(losses_detailed) > 2 else "0",
            'others': other_losses
        },
        'fights': []
    }

    fight_rows = xml.xpath("//table[@class='new_table fighter']/tr[not(@class='table_head')]")
    for row in fight_rows:
        referee = row.xpath("td[4]/span/a/text()")
        fight = {
            'name': safe_xpath(row, "td[3]/a/descendant-or-self::*/text()"),
            'date': safe_xpath(row, "td[3]/span/text()"),
            'url': BASE_URL_SHERDOG.rstrip('/') + safe_xpath(row, "td[3]/a/@href"),
            'result': safe_xpath(row, "td[1]/span/text()"),
            'method': safe_xpath(row, "td[4]/b/text()"),
            'referee': referee[0] if referee else "",
            'round': safe_xpath(row, "td[5]/text()"),
            'time': safe_xpath(row, "td[6]/text()"),
            'opponent': safe_xpath(row, "td[2]/a/text()")
        }
        fighter['fights'].append(fight)
    return fighter

def get_ufc_info(url: str) -> dict:
    try:
        response = session.get(url, headers=DEFAULT_HEADERS)
        response.raise_for_status()
    except req.RequestException as e:
        logger.error(f"Error fetching UFC URL {url}: {e}")
        raise

    xml = html.document_fromstring(response.content)
    distance = xml.xpath("//div[@class='c-stat-3bar__value']/text()")
    stats = xml.xpath("//div[@class='c-stat-compare__number']/text()")
    bio = xml.xpath("//div[@class='c-bio__text']/text()")
    str_tds = [item.text.strip() if item.text else "0" for item in xml.xpath("//dd")]
    attempted = str_tds[1] if len(str_tds) > 1 else "0"
    landed = str_tds[0] if len(str_tds) > 0 else "0"
    takedowns_attempted = str_tds[3] if len(str_tds) > 3 else "0"
    takedowns_landed = str_tds[2] if len(str_tds) > 2 else "0"
    striking_defense = stats[4].strip() if len(stats) > 4 else "0"
    strikes_per_minute = stats[0].strip() if len(stats) > 0 else "0"
    takedown_defense = stats[5].strip() if len(stats) > 5 else "0"
    subs_per_15min = stats[3].strip() if len(stats) > 3 else "0"
    standing = distance[0].split(" ")[0] if len(distance) > 0 and distance[0] else "0"
    clinch = distance[1].split(" ")[0] if len(distance) > 1 and distance[1] else "0"
    ground = distance[2].split(" ")[0] if len(distance) > 2 and distance[2] else "0"
    status = bio[0].strip() if len(bio) > 0 else "Unknown"
    fight_style = bio[3].strip() if len(bio) > 3 else "Unknown"
    octagondebut = bio[8].strip() if len(bio) > 8 else "Unknown"
    reach = bio[9].strip() if len(bio) > 9 else "Unknown"
    legreach = bio[10].strip() if len(bio) > 10 else "Unknown"

    fighter_stats = {
        'status': status,
        'fight_style': fight_style,
        'octagondebut': octagondebut,
        'reach': reach,
        'legreach': legreach,
        'strikes': {
            'attempted': attempted,
            'landed': landed,
            'standing': standing,
            'clinch': clinch,
            'ground': ground,
            'striking defense': striking_defense,
            'strikes per minute': strikes_per_minute
        },
        'takedowns': {
            'attempted': takedowns_attempted,
            'landed': takedowns_landed,
            'takedown defense': takedown_defense,
            'subs per 15min': subs_per_15min
        }
    }
    return fighter_stats

def get_ufc_stats_link(query: str) -> str:
    try:
        possible_urls = list(search(query + " " + BASE_URL_UFCSTATS, num_results=5))
    except Exception as e:
        logger.error(f"Error during Google search for UFC Stats link with query '{query}': {e}")
        raise

    for url in possible_urls:
        if "ufcstats.com/fighter-details/" in url:
            return url
    raise Exception("UFC Stats link not found!")

def get_ufc_stance(link: str) -> str:
    try:
        response = req.get(link, headers=DEFAULT_HEADERS)
        response.raise_for_status()
    except req.RequestException as e:
        logger.error(f"Error fetching UFC Stats URL {link}: {e}")
        return ""
    
    doc = html.fromstring(response.content)
    stance = safe_xpath(doc, "//li[i[contains(text(), 'STANCE:')]]/text()[normalize-space()]")
    return stance

def get_sherdog_link(query: str, max_retries: int = MAX_RETRIES) -> str:
    search_query = f"{query} Sherdog"
    retry_count = 0

    while retry_count < max_retries:
        try:
            search_results = list(search(search_query, num_results=1))
            if search_results:
                for url in search_results:
                    if "sherdog.com/fighter/" in url and "/news/" not in url:
                        return url
                logger.warning(f"No valid Sherdog fighter profile URL found for query: {query}")
            else:
                logger.warning(f"No search results found for query: {query}")
        except Exception as e:
            logger.error(f"Error retrieving search results for '{query}': {e}")
        retry_count += 1
        backoff_delay = random.uniform(1, 5) * (2 ** retry_count)
        logger.info(f"Retrying in {backoff_delay:.2f} seconds... (attempt {retry_count}/{MAX_RETRIES})")
        time.sleep(backoff_delay)

    raise Exception(f"Sherdog link not found for query: {query}")

def get_ufc_link(query: str) -> str:
    try:
        possible_urls = list(search(query + " UFC.com", num_results=5))
    except Exception as e:
        logger.error(f"Error during Google search for UFC link with query '{query}': {e}")
        raise

    for url in possible_urls:
        if BASE_URL_UFC.strip('/') + "/athlete/" in url:
            return url
    raise Exception("UFC link not found!")

def get_fighter(query: str) -> dict:
    sherdog_link = get_sherdog_link(query)
    ufc_link = get_ufc_link(query)
    
    fighter = parse_sherdog_fighter(sherdog_link)
    fighter.update(get_ufc_info(ufc_link))
    
    try:
        ufc_stats_link = get_ufc_stats_link(query)
        fighter['stance'] = get_ufc_stance(ufc_stats_link)
    except Exception as e:
        logger.error(f"Error retrieving UFC stance for query '{query}': {e}")
        fighter['stance'] = ""
    
    return fighter

def get_upcoming_event_links_inner() -> list:
    """
    Helper function to retrieve the raw list of upcoming event links.
    """
    url = BASE_URL_UFC + 'events'
    try:
        response = session.get(url, headers=DEFAULT_HEADERS)
        response.raise_for_status()
    except req.RequestException as e:
        logger.error(f"Error fetching UFC events page: {e}")
        raise

    xml = html.document_fromstring(response.content)
    links = xml.xpath("//details[@id='events-list-upcoming']/div/div/div/div/div/section/ul/li/article/div[1]/div/a/@href")
    return [BASE_URL_UFC.rstrip('/') + "/" + x.lstrip('/') for x in links]

def get_upcoming_event_links() -> list:
    return get_upcoming_event_links_inner()

def get_ufc_link_event(query: str) -> str:
    try:
        possible_urls = list(search(query + " UFC", num_results=5))
    except Exception as e:
        logger.error(f"Error during Google search for UFC event with query '{query}': {e}")
        raise

    for url in possible_urls:
        if "ufc.com/event/" in url:
            return url
    raise Exception("UFC event link not found!")

def get_ranking(fight, corner: str) -> str:
    if corner == 'red':
        path = "div/div/div/div[2]/div[2]/div[2]/div[1]/span/text()"
    else:
        path = "div/div/div/div[2]/div[2]/div[2]/div[2]/span/text()"
    try:
        ranking_text = fight.xpath(path)[0]
        return ranking_text[1:] if ranking_text else "Unranked"
    except IndexError:
        return "Unranked"

def get_name(fight, corner: str) -> str:
    if corner == 'red':
        path = "div/div/div/div[2]/div[2]/div[5]/div[1]/a/span/text()"
    else:
        path = "div/div/div/div[2]/div[2]/div[5]/div[3]/a/span/text()"
    name_parts = fight.xpath(path)
    name = " ".join(name_parts).strip()
    if not name:
        fallback_path = path.replace("/span", "")
        name = " ".join(fight.xpath(fallback_path)).strip()
    return name

def parse_event(url: str, past: bool = True) -> dict:
    try:
        response = session.get(url, headers=DEFAULT_HEADERS)
        response.raise_for_status()
    except req.RequestException as e:
        logger.error(f"Error fetching UFC event URL {url}: {e}")
        raise

    xml = html.document_fromstring(response.content)
    prefix = safe_xpath(xml, "//div[@class='c-hero__header']/div[1]/div/h1/text()")
    names = xml.xpath("//div[@class='c-hero__header']/div[2]/span/span/text()")
    event_name = f"{prefix}: {names[0].strip()} vs. {names[-1].strip()}" if names else prefix
    timestamp = xml.xpath("//div[@class='c-hero__bottom-text']/div[1]/@data-timestamp")
    try:
        date = dt.datetime.fromtimestamp(int(timestamp[0])).strftime("%Y-%m-%d") if timestamp else ""
    except ValueError:
        date = ""
    location_text = safe_xpath(xml, "//div[@class='c-hero__bottom-text']/div[2]/div/text()")
    location_parts = location_text.split(",") if location_text else ["", ""]
    venue = location_parts[0].strip() if location_parts[0] else ""
    loc = location_parts[1].strip() if len(location_parts) > 1 else ""

    event = {
        'name': event_name,
        'date': date,
        'location': loc,
        'venue': venue,
        'fights': []
    }
    
    fights_html = xml.xpath("//div[@class='fight-card']/div/div/section/ul/li")
    for fight in fights_html:
        weightclass_text = safe_xpath(fight, "div/div/div/div[2]/div[2]/div[1]/div[2]/text()")
        fight_details = {
            'weightclass': weightclass_text[:-5] if weightclass_text else "",
            'red corner': {
                'name': get_name(fight, 'red'),
                'ranking': get_ranking(fight, 'red'),
                'odds': safe_xpath(fight, "div/div/div/div[4]/div[2]/span[1]/span/text()"),
                'link': safe_xpath(fight, "div/div/div/div[2]/div[2]/div[5]/div[1]/a/@href")
            },
            'blue corner': {
                'name': get_name(fight, 'blue'),
                'ranking': get_ranking(fight, 'blue'),
                'odds': safe_xpath(fight, "div/div/div/div[4]/div[2]/span[3]/span/text()"),
                'link': safe_xpath(fight, "div/div/div/div[2]/div[2]/div[5]/div[3]/a/@href")
            }
        }
        if past:
            result = fight.xpath("div/div/div/div[2]//div[@class='c-listing-fight__outcome-wrapper']/div/text()")
            method = fight.xpath("div//div[@class='c-listing-fight__result-text method']/text()")
            finished_round = fight.xpath("div//div[@class='c-listing-fight__result-text round']/text()")
            finished_time = fight.xpath("div//div[@class='c-listing-fight__result-text time']/text()")
            
            fight_details['round'] = finished_round[0] if finished_round else ""
            fight_details['time'] = finished_time[0] if finished_time else ""
            fight_details['method'] = method[0] if method else ""
            if result and len(result) >= 2:
                fight_details['red corner']['result'] = result[0].strip()
                fight_details['blue corner']['result'] = result[1].strip()
            else:
                fight_details['red corner']['result'] = ""
                fight_details['blue corner']['result'] = ""
        event['fights'].append(fight_details)
    return event

def get_upcoming_events() -> dict:
    links = get_upcoming_event_links()
    results = {}
    for url in links:
        try:
            event = parse_event(url, past=False)
            results[event['name']] = event
        except Exception as e:
            logger.error(f"Error parsing event at {url}: {e}")
    return results

def get_event(query: str) -> dict:
    link = get_ufc_link_event(query)
    return parse_event(link)
