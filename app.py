# -*- coding: utf-8 -*-
"""
HTML Transformer — 3 админки (Rocketplay / Winspirit-Luckyhills / Zoome)

Ключевые требования:
- Чистый HTML: никаких <style> и inline style=
- Zero-invention: строго использовать ТОЛЬКО текст пользователя (+ анкоры по правилам)
- Экранирование спецсимволов: ТОЛЬКО для Winspirit/Luckyhills ({ } @ $ | / € % & → {'символ'}), '/' лишь между цифрами (24/7)
- Встроен ПОЛНЫЙ Rocketplay TARGET HTML TEMPLATE (1:1) — подставляется в промпт и автоматически очищается от стилей
- DOM-превью (JSON) для удобной постобработки
"""

from __future__ import annotations

import os
import re
import json
from datetime import datetime
from typing import Dict, Tuple, Optional, List

import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI

# Опционально для DOM-превью
try:
    from bs4 import BeautifulSoup, NavigableString, Comment
except Exception:
    BeautifulSoup = None

APP_TITLE = "🧩 HTML Transformer"

# === Обязательный секрет ===
OPENAI_KEY: str = st.secrets.get("OPENAI_API_KEY", "")

# === Модель/превью ===
MODEL: str = os.getenv("HTML_TRANSFORMER_MODEL", "gpt-4.1-mini")
PREVIEW_HEIGHT: int = int(os.getenv("HTML_PREVIEW_HEIGHT", "1200"))

# Плейсхолдеры
PLACEHOLDER = "Тут должен быть текст который вставил юзер"   # контент пользователя
ANCHORS_PLACEHOLDER = "<<<ANCHORS>>>"                       # блок анкоров
TARGET_TEMPLATE_PLACEHOLDER = "<<<TARGET_HTML_TEMPLATE>>>"  # блок Rocketplay-шаблона

# ---------- ПРОМПТЫ (чистый HTML, zero-invention) ----------

# 1) Rocketplay — строго по готовому каркасу (подставляем ПОЛНЫЙ шаблон), без стилей и без выдумок
HTML_PROMPT: str = r"""You are a rigorous HTML transformer in STRICT mode.
Return ONLY one HTML block. No explanations, no code fences. The first character must be "<" and the last must be ">".
It must start with <div class="markup-seo-page"> and end with </div>.
Keep the TARGET HTML TEMPLATE structure 100% identical (same tags, order, attributes), but NEVER output any <style> tag nor any style="...".
Zero-invention: use ONLY words present in RAW CONTENT (and the anchor texts when allowed). Do NOT translate, summarise, paraphrase, or add new words.
If RAW CONTENT is insufficient for some inner text, keep the template’s current inner text as-is.

ANCHORS (OPTIONAL) — LINK TEXTS ONLY:
- If a list of anchors is provided below, use their TEXTS to set the INNER TEXT of the existing 7 <a> tags IN ORDER (first 7 anchors only).
- Do NOT change any href in the template. If fewer than 7 anchors are provided, keep remaining link texts from RAW CONTENT or leave as-is. Ignore extras.
- If an anchor item includes its own href, IGNORE it here (hrefs are fixed in the template).

[ANCHORS LIST]
<<<ANCHORS>>>

[RAW CONTENT]
Тут должен быть текст который вставил юзер

[TARGET HTML TEMPLATE]
<<<TARGET_HTML_TEMPLATE>>>
"""

# 2) WinSpirit / LuckyHills — строгий конвертер: Meta + чистый HTML; ТОЛЬКО здесь экранируем спецсимволы (препроцессинг)
HTML_PROMPT_WS_LH: str = r"""
You are a formatting engine in STRICT MODE. Do not translate, summarise, paraphrase, or add any new words, numbers, brands, or claims.
Use ONLY wording already present in the input (and the given anchors where allowed). NEVER output any <style> tag nor style="...".
Do not escape or unescape characters yourself — keep characters exactly as they appear in INPUT (they may already be escaped).

ANCHORS (OPTIONAL) — SAFE WRAP:
- Wrap VERBATIM occurrences of provided anchor TEXTS with <a>.
- If an anchor has href, use it as-is; if no href, keep plain text. Do not invent hrefs.
- No casing/punctuation changes. If a text is not found, skip it.

[ANCHORS LIST]
<<<ANCHORS>>>

INPUT:
{{INPUT_TEXT}}   # arbitrary user text, any language (may already contain tokens like {'@'}, {'/'} etc.)

OUTPUT — STRICT SHAPE (ONLY this, no commentary, no fences):
1) Meta Title: <≤65 chars using ONLY input words; no new info>
2) Meta Description: <150–160 chars using ONLY input words; no new info>
3) Then the content HTML, starting exactly like:
   <h1>…</h1>
   <p>…</p>
   <section>
     <h2>…</h2>
     <p>…</p>
     <!-- optional <h3>, lists, tables, links -->
   </section>
   <!-- additional <section> blocks as needed -->

RULES (ZERO INVENTION):
- Language: keep as in input.
- Headings: use a clear title line verbatim for <h1>; if none, use the first non-empty line verbatim.
- Paragraphs & lists: convert text blocks to <p>. Steps/bullets → <ul>/<ol> with <li>, preserving exact wording.
- Links: if the input contains explicit URLs or "/path", wrap exactly those substrings as <a href="…">…</a> with the same visible text.
- Tables: if tabular intent is clear (header + rows OR consistent columns), output a plain table without any styles:
  <table><tbody><tr><td><p>cell text as in input</p></td>…</tr>…</tbody></table>
- Numbers/symbols: keep exactly as-is. Do not normalise punctuation or symbols. Do not change existing {'.'} tokens.
"""

# 3) Zoome — секционный вывод без стилей, zero-invention
HTML_PROMPT_ZOOME: str = r"""
You are a formatting engine. Convert ANY input text into an HTML snippet following the Zoome-like sectioning.
Zero-invention: do NOT translate, summarise, paraphrase, or add new words. Use ONLY text present in the input (and anchors where allowed).
NEVER output any <style> tag nor style="...".

ANCHORS (OPTIONAL):
- For each provided anchor TEXT, wrap its first VERBATIM occurrence with <a> using the given href (if present). If no href, keep plain text. No changes to wording/casing. If not found, skip.

[ANCHORS LIST]
<<<ANCHORS>>>

INPUT:
{{INPUT_TEXT}}

OUTPUT — STRICT SHAPE (snippet only, no commentary):
- One or more <section> blocks.
- The first <section> MUST contain the main <h1> verbatim from the first clear title line; if no title line, use the first non-empty line.
- Intro paragraphs after <h1> as <p>.
- Standalone topic lines → new <section> with <h2>; nested topics may use <h3>.
- Bullets/steps → <ul>/<ol> with <li>.
- If the input ends with an FAQ-like list, you MAY output <h2>FAQ</h2> then pairs <h3>Q</h3><p>A</p>.
- Tables (if clearly tabular) → plain HTML table (no styles):
  <section><table><tbody><tr><td><p>Header</p></td>…</tr><tr><td><p>Cell</p></td>…</tr></tbody></table></section>
- Numbers/symbols: keep exactly as-is.
"""

# ---------- /ПРОМПТЫ КОНЕЦ ----------

PROMPTS: Dict[str, str] = {
    "Rocketplay": HTML_PROMPT,
    "Winspirit/Luckyhills": HTML_PROMPT_WS_LH,
    "Zoome": HTML_PROMPT_ZOOME,
}

# ----------------- ПОЛНЫЙ Rocketplay TARGET HTML TEMPLATE (1:1 из твоего примера) -----------------
ROCKETPLAY_TEMPLATE_DEFAULT = """<div class="markup-seo-page"> <style> .markup-seo-page { table { width: 100%; border-collapse: collapse; } td { border: 2px solid gray; padding: 8px; text-align: left; } ol { list-style-type: decimal; } .fe-button { color: var(--color-button-text-primary); text-decoration: none; } @media screen and (max-width: 600px) { td { border-width: 1px; padding: 4px; font-size: 11px; } } .seo-container { justify-items: stretch; } } </style> <h1>Rocketplay Online Casino Deutschland - Die beste Adresse für Spieler aus Deutschland und Österreich</h1> <p>Willkommen im Rocketplay Casino - dem führenden Online Casino Deutschland для Spieler aus Deutschland und Österreich! In unserem Casino Rocketplay erwarten Sie hochwertige Spiele, attraktive Boni und ein sicheres Spielerlebnis rund um die Uhr. Entdecken Sie jetzt die Welt des Premium-Glücksspiels!</p> <h2>Einführung in das Online Casino</h2> <p>Das Online Casino ist eine moderne Plattform, die es Spielern ermöglicht, eine Vielzahl von Glücksspielen bequem von zu Hause aus oder unterwegs zu genießen. In einem Online Casino können Sie beliebte Spiele wie Slots, Roulette, Blackjack und Poker spielen. Diese Spiele stammen von renommierten Anbietern wie Evolution, Play'N GO, Hacksaw Gaming und Pragmatic Play, die für ihre hochwertigen und unterhaltsamen Spiele bekannt sind.</p> <p>Spieler können auf diese Spiele über das Internet zugreifen и um Echtgeld spielen, was das Online Casino zu einer attraktiven Alternative zu traditionellen Spielhallen macht. In Deutschland sind Online Casinos legal und unterliegen den strengen Vorschriften des Glücksspielstaatsvertrags, der sicherstellt, что alle Spiele fair und sicher ablaufen. Dies bietet den Spielern die Gewissheit, dass sie в einer regulierten und geschützten Umgebung spielen.</p> <h2>Warum unser Online Casino die beste Wahl ist</h2> <p>Als etabliertes Online Casino bietet Rocketplay ein erstklassiges Spielerlebnis für alle Spieler. Unser Casino zeichnet sich durch folgende Vorteile aus:</p> <ul> <li>Große Spieleauswahl - Über 3.000 hochwertige Casino Spiele von renommierten Anbietern</li> <li>Sichere Lizenz - Vollständig lizenziert durch Curacao</li> <li>Attraktive Bonusangebote - Großzügige Willkommensboni und regelmäßige Promotionen</li> <li>Schnelle Auszahlungen - Erhalten Sie Ihre Gewinne sicher und zügig</li> <li>Mehrsprachiger Support - Kundendienst in deutscher Sprache rund um die Uhr verfügbar</li> </ul> <p>In unserem Online Casino finden Sie alles, was das Spielerherz begehrt - von klassischen Top Spielautomaten bis hin zu spannenden Live-Spielen mit echten Dealern. Egal ob Sie aus Deutschland oder Österreich zu uns kommen, wir garantieren ein sicheres и unterhaltsames Spielerlebnis.</p> <h2>Online Casino Deutschland - Die besten Spiele bei Rocketplay</h2> <p>In unserem Online Casino Deutschland haben wir eine sorgfältig kuratierte Auswahl an Spielen zusammengestellt, die speziell auf die Vorlieben deutscher und österreichischer Spieler abgestimmt ist. Unsere Spielhallen bieten eine beeindruckende Vielfalt an Unterhaltungsmöglichkeiten, darunter beliebte Automatenspiele wie 'Book of Ra Magic' von namhaften Herstellern wie Novomatic.</p> <h3>Populäre Spielautomaten in unserem Casino</h3> <p>In unseren Online Spielotheken finden Sie <a href="/de/pokies/all"> beste Spielautomaten für Spieler aus Deutschland und Österreich</a>. Von klassischen Frucht Spielautomaten bis hin zu modernen Videoslots mit aufregenden Bonusfunktionen - bei uns wird jeder Spieler fündig.</p> <p>Zu den beliebtesten Slots in unserem Casino zählen:</p> <table> <tbody> <tr> <td> <p>Top Spielautomaten</p> </td> <td> <p>Anbieter</p> </td> <td> <p>Besonderheiten</p> </td> </tr> <tr> <td> <p>Wings of Horus</p> </td> <td> <p>Hacksaw Gaming</p> </td> <td> <p>Expandierendes Symbol, Freispiele</p> </td> </tr> <tr> <td> <p>Big Bass Bonanza</p> </td> <td> <p>Pragmatic Play</p> </td> <td> <p>Fisch-Sammel-Funktion, Multiplikatoren</p> </td> </tr> <tr> <td> <p>Sweet Bonanza</p> </td> <td> <p>Pragmatic Play</p> </td> <td> <p>Tumble-Feature, Freispiele mit Multiplikatoren</p> </td> </tr> <tr> <td> <p>Book of Dead</p> </td> <td> <p>Play’n GO</p> </td> <td> <p>Freispiele mit erweiterndem Symbol</p> </td> </tr> <tr> <td> <p>John Hunter and the Tomb of the Scarab Queen</p> </td> <td> <p>Pragmatic Play</p> </td> <td> <p>Abenteuer-Thema, Freispiele</p> </td> </tr> </tbody> </table> <p>Für Spieler, die immer auf dem neuesten Stand bleiben möchten, bieten wir regelmäßig <a href="/de/pokies/new"> neue Spielautomaten für Spieler aus Deutschland und Österreich</a> an. So können Sie stets die aktuellsten Spielinnovationen entdecken und genießen.</p> <h3>Big Bass Bonanza und andere beliebte Slots</h3> <p>Big Bass Bonanza gehört zu den absoluten Favoriten в unserem Online Casino. Dieser unterhaltsame Angel-Slot begeistert durch sein einzigartiges Spielprinzip и die Chance auf große Gewinne. Das Spiel bietet spannende Freispiele mit Multiplikatoren и die Möglichkeit, zusätzliche Fisch-Symbole zu sammeln.</p> <p>Ein weiteres Beispiel für die Vielfalt unserer angebotenen Slots ist 'Diamond Link: Mighty Elephant', das durch seine aufregenden Features и Themen überzeugt. Die Big Bass Serie hat sich aufgrund ihrer eingängigen Spielmechanik и des amüsanten Themas zu einem echten Hit entwickelt. Spieler aus Deutschland и Österreich schätzen besonders die faire Auszahlungsquote и die regelmäßigen Gewinnchancen.</p> <h3>Spielautomaten mit hoher Volatilität für risikobereite Spieler</h3> <p>Für Spieler, die bereit sind, ein höheres Risiko einzugehen, bieten wir <a href="/de/pokies/high-volatility"> Spielautomaten mit hoher Volatilität</a> an. Diese Spiele bieten die Chance auf besonders große Gewinne, auch wenn diese seltener auftreten als bei Online Slots mit niedrigerer Volatilität.</p> <p>Hochvolatile Slots sind ideal für geduldige Spieler, die auf den großen Gewinn warten können. Ein Beispiel hierfür ist 'Gates of Olympus', ein göttlicher Online Slot, der außergewöhnliche Themen, hohe Gewinnmöglichkeiten und Freispiele bietet. In unserem Casino finden Sie eine große Auswahl an diesen spannenden Spielen, die für den besonderen Nervenkitzel sorgen.</p> <h2>Online Spielotheken Vergleich - Darum überzeugt Rocketplay</h2> <p>Im Vergleich zu anderen Online Spielotheken hebt sich unser Casino Rocketplay durch zahlreiche Vorteile ab. Ein umfassender Online Casino Vergleich zeigt, dass wir durch schnelle Auszahlungen и eine große Auswahl an Online Slots überzeugen. Wir haben uns als eine der führenden Online Spielhallen im deutschsprachigen Raum etabliert и bieten ein Spielerlebnis der Extraklasse. Unsere Vorteile im Überblick:</p> <ol> <li>Umfangreiche Spieleauswahl - Über 3.000 Spiele von mehr als 40 Anbietern</li> <li>Attraktive Bonusangebote - Regelmäßige Promotionen и ein großzügiges VIP-Programm</li> <li>Sichere Zahlungsmethoden - Schnelle Ein- и Auszahlungen mit verschiedenen Optionen</li> <li>Hervorragender Kundendienst - Support rund um die Uhr in deutscher Sprache</li> <li>Optimierte mobile Version - Spielen Sie unterwegs auf Ihrem Smartphone oder Tablet</li> <li>Sicherheit и Legalität - Unsere Plattform steht unter der Aufsicht der Gemeinsamen Glücksspielbehörde der Länder, die für die Überwachung и Lizenzierung von Online-Spielotheken в Deutschland zuständig ist. Dies garantiert ein sicheres und legales Spielumfeld.</li> </ol> <p>Positive Casino Tests bestätigen regelmäßig die Qualität unseres Angebots. In unabhängigen Online Casino Tests schneidet Rocketplay regelmäßig als eines der Top Online Casinos für deutsche и österreichische Spieler ab.</p> <h3>Online Casino Seiten im Vergleich</h3> <p>Im umfangreichen Markt der Online Casino Seiten kann es schwierig sein, den Überblick zu behalten. Rocketplay sticht durch sein ausgewogenes Angebot и die Fokussierung auf die Bedürfnisse deutschsprachiger Spieler hervor.</p> <p>Unsere Casino Seiten wurden speziell für Spieler aus Deutschland und Österreich оптимiert. Die Benutzeroberfläche ist intuitiv gestaltet и ermöglicht einen einfachen Zugang zu allen Bereichen unseres Casinos. Besonders wichtig ist uns die Sicherheit и Legalität der Einzahlungen, damit Ihr online casino geld stets geschützt ist и Sie sich keine Sorgen um die Rückforderung machen müssen.</p> <h3>Internet Casinos и ihre Besonderheiten</h3> <p>Online Casinos haben в den letzten Jahren stark an Beliebtheit gewonnen. Als modernes und innovatives Casino setzen wir bei Rocketplay на die neuesten Technologien, um ein optimales Spielerlebnis zu gewährleisten.</p> <p>Unsere Online Spielbank ist eine sichere und legale Plattform, die den strengen gesetzlichen Vorgaben entspricht и Schutzmaßnahmen für die Daten der Spieler implementiert hat. Im Gegensatz zu landbasierten Spielhallen bietet unser Online Casino den Vorteil, dass Sie rund um die Uhr и von überall aus spielen können. Zudem profitieren Sie von einer deutlich größeren Spielauswahl и attraktiveren Bonusangeboten.</p> <h2>Freispiele и Boni в unserem Casino</h2> <p>Ein besonderes Highlight в unserem Online Casino sind die attraktiven Freispiele и Bonusangebote. Als neuer Spieler profitieren Sie von einem großzügigen Willkommensbonus, während treue Kunden regelmäßig mit Reload-Boni, Freispielen и der Chance auf cash-Gewinne belohnt werden.</p> <h3>Willkommensbonus для Neukunden</h3> <p>Als Neukunde в unserem Casino Rocketplay erhalten Sie einen attraktiven Willkommensbonus:</p> <table> <tbody> <tr> <td> <p>Einzahlung</p> </td> <td> <p>Bonus</p> </td> <td> <p>Freispiele</p> </td> <td> <p>Umsatzbedingungen</p> </td> </tr> <tr> <td> <p>1. Einzahlung</p> </td> <td> <p>100% bis zu 1000€</p> </td> <td> <p>100 Freispiele</p> </td> <td> <p>40х Bonus</p> </td> </tr> <tr> <td> <p>2. Einzahlung</p> </td> <td> <p>200% bis zu 1000€</p> </td> <td> <p>–</p> </td> <td> <p>40x Bonus</p> </td> </tr> </tbody> </table> <p>Mit diesem Bonuspaket können Sie Ihr Startguthaben erheblich erhöhen и haben die Möglichkeit, unser umfangreiches Spielangebot ausgiebig zu erkunden. Zusätzlich bieten unsere premium mitgliedschaften Zugang zu den höchsten Auszahlungsquoten и exklusiven Boni, die Ihr Spielerlebnis weiter aufwerten.</p> <h3>Gratis Freispiele и regelmäßige Promotionen</h3> <p>Neben dem Willkommensbonus bieten wir regelmäßig Gratis Freispiele и andere Promotionen an. Diese Aktionen werden wöchentlich aktualisiert и bieten immer neue Möglichkeiten, von zusätzlichen Vorteilen zu profitieren и dabei zu gewinnen.</p> <p>Unsere Freispiele können bei ausgewählten Spielautomaten eingesetzt werden и bieten die Chance на echte Gewinne ohne eigenen Einsatz. Die genauen Bedingungen finden Sie jeweils в der Beschreibung der Aktion.</p> <h3>Spielothek Bonus für treue Spieler</h3> <p>Unser Spielothek Bonus для Stammkunden umfasst regelmäßige Reload-Boni, Cashback-Aktionen und exklusive Turniere. Je aktiver Sie в unserem Casino spielen, desto mehr Vorteile genießen Sie.</p> <p>Ein besonderes Highlight ist unser VIP-Programm с verschiedenen Stufen и exklusiven Vorteilen:</p> <ul> <li>Bronze - 5% wöchentlicher Cashback, schnellere Auszahlungen</li> <li>Silber - 7% wöchentlicher Cashback, persönlicher Account Manager</li> <li>Gold - 10% wöchentlicher Cashback, erhöhte Einzahlungs- und Auszahlungslimits</li> <li>Platin - 15% wöchentlicher Cashback, exklusive Boni и Promotionen</li> <li>Diamond - 20% wöchentlicher Cashback, VIP-Events и individuelle Angebote</li> </ul> <p>Ein weiteres Beispiel für attraktive Gewinnmöglichkeiten ist unser 'Cash Connection' Jackpot-Spiel, bei dem feste Jackpot-Gewinne auf Sie warten.</p> <p>Die Premium Mitgliedschaft в unserem VIP-Club bietet zusätzliche Vorteile wie persönliche Betreuung, höhere Limits и exklusive Boni mit Freispiele, die auf Ihre individuellen Vorlieben abgestimmt sind.</p> <h2>Online Casino в Deutschland - Sicherheit и Seriosität</h2> <p>Als Online Casino в Deutschland legen wir größten Wert auf Sicherheit и Seriosität. Rocketplay verfügt über eine gültige Glücksspiellizenz aus Curacao, die strenge Anforderungen an den Spielerschutz и die Fairness der angebotenen Spiele stellt. Online Spielbanken sind sichere und legale Plattformen, die speziell optimierte Spiele von führenden Software-Herstellern anbieten.</p> <h3>Sicheres Spielen bei Rocketplay</h3> <p>Die Sicherheit unserer Spieler hat für uns oberste Priorität. Wir setzen modernste SSL-Verschlüsselungstechnologie ein, um alle Daten и Transaktionen zu schützen. Zudem arbeiten wir nur mit renommierten Zahlungsdienstleistern zusammen, die höchste Sicherheitsstandards garantieren.</p> <p>Alle Spiele в unserem Casino werden regelmäßig von unabhängigen Prüfinstituten auf Fairness getestet. So können Sie sicher sein, dass bei uns alles mit rechten Dingen zugeht и jeder Spieler die gleichen Chancen auf Gewinne hat.</p> <h3>Verantwortungsvolles Spielen</h3> <p>We fördern verantwortungsvolles Glück и bieten verschiedene Tools zur Spielkontrolle an:</p> <ul> <li>Einzahlungslimits</li> <li>Spielzeitbegrenzungen</li> <li>Selbstausschlussoptionen</li> <li>Realitätschecks während des Spiels</li> <li>Selbsteinschätzungstests</li> </ul> <p>Die Spielteilnahme в нашем Casino soll в erster Linie Spaß machen и der Unterhaltung dienen. Wir ermutigen alle Spieler, ihre Grenzen zu kennen и innerhalb dieser zu spielen.</p> <h2>Live Casino - Das authentische Casinoerlebnis</h2> <p>Für Spieler, die die Atmosphäre eines echten Casinos schätzen, bieten wir ein erstklassiges Live Casino. Здесь können Sie <a href="/de/live/all"> Spielen Sie Live-Casino mit echten Live-Dealern</a> und die authentische Casino-Atmosphäre von zu Hause aus genießen. Zusätzlich bieten wir eine breite Palette an Automatenspielen, darunter beliebte Titel wie 'Fancy Fruits' von Bally Wulff, die sowohl классические als auch moderne Hits umfassen.</p> <h3>Live-Blackjack mit echten Dealern</h3> <p>Blackjack-Enthusiasten kommen в unserem Live-Bereich voll auf ihre Kosten. Bei uns können Sie <a href="/de/live/blackjack"> Live-Blackjack mit echtem Croupier для Spieler aus Deutschland und Österreich</a> an verschiedenen Tischen mit unterschiedlichen Einsatzlimits spielen.</p> <p>Unsere professionellen Dealer sorgen für ein authentisches Spielerlebnis und stehen Ihnen bei Fragen jederzeit zur Verfügung. Die hochwertige Übertragung in HD-Qualität und die interaktiven Funktionen machen das Spiel besonders unterhaltsam.</p> <h3>Online-Roulette Live erleben</h3> <p>Ein weiteres Highlight в нашем Live Casino ist Roulette. Sie können <a href="/de/live/roulette"> Spielen Sie Online-Roulette и Live-Roulette</a> в различных Varianten, darunter Europäisches, Amerikanisches и Französisches Roulette. Ein weiteres Beispiel für die Vielfalt der angebotenen Spiele ist 'Diamond Link: Mighty Sevens', ein beliebtes Jackpot-Spiel mit festen Jackpots и spannenden Gewinnmechaniken.</p> <p>Die Spannung, wenn die Kugel im Roulettekessel rollt, ist auch beim Online-Spiel zu spüren. Durch die Live-Übertragung и die Interaktion mit dem Dealer entsteht ein immersives Spielerlebnis, das dem einer echten Spielbank sehr nahe kommt.</p> <h3>Baccarat и weitere Live-Spiele</h3> <p>Komplettiert wird unser Live-Angebot durch <a href="/de/live/baccarat"> Spiele Baccarat-Spiele</a> и weitere klassische Casinospiele. Baccarat erfreut sich besonders bei erfahrenen Spielern großer Beliebtheit и bietet spannende Spielrunden mit echten Dealern.</p> <p>Neben diesen Klassikern finden Sie в нашем Live Casino auch innovative Game Shows и spezielle VIP-Tische для höhere Einsätze. So ist für jeden Geschmack и jedes Budget etwas dabei. Darüber hinaus bieten wir eine Vielzahl von Spielautomaten, darunter beliebte Titel wie 'Rich Wilde and the Book of Dead', die für ihre abenteuerlichen Themen и spannenden Spielmechaniken bekannt sind.</p> <h2>Schritt-für Schritt zum RocketPlay Casino Konto</h2> <p>Um Zugriff auf die Echtgeld Casino Spiele online zu erhalten, müssen Sie ein Konto erstellen. Die RocketPlay Casino Registrierung ist dabei innerhalb weniger Momente abgeschlossen. Befolgen Sie dazu einfach die folgenden Schritte: </p> <ol> <li>Webseite aufrufen: Besuchen Sie die offizielle RocketPlay Casino Webseite и klicken Sie auf „Registrieren“,</li> <li>Daten angeben: Sie werden nun gebeten, Daten zu Ihrer Person anzugeben. Dazu gehören Datum, Alter и auch Adresse. </li> <li>E-Mail-Bestätigung: Sie erhalten nun eine E-Mail. Klicken Sie dort auf den Link, um Ihr Konto zu bestätigen. </li> <li>Einzahlung tätigen: Nun können Sie Ihre erste Einzahlung tätigen, um die Echtgeld-Spiele ausprobieren zu können. </li> </ol> <p>Seien Sie sich jedoch bewusst, dass Sie vor Ihrer ersten RocketPlay Casino Auszahlung Ihre Identität verifizieren müssen. So gehen wir sicher, dass Sie wirklich die Person sind, für die Sie sich ausgeben. Laden Sie dazu eine Kopie Ihres Ausweises sowie einen Адресnachweis hoch. Das ermöglicht uns, Ihnen die sicherste und beste Online Casino Erfahrung zu ermöglichen. </p> <h2>Casino spielen bei Rocketplay - Zahlungsmethoden und Support</h2> <p>Casino spielen bei Rocketplay ist nicht nur unterhaltsam, sondern auch einfach und sicher. Wir bieten verschiedene Zahlungsmethoden an, die schnelle und sichere Transaktionen gewährleisten. Zahlungsoptionen im Überblick:</p> <table> <tbody> <tr> <td> <p>Zahlungsmethode</p> </td> <td> <p>Mindesteinzahlung</p> </td> <td> <p>Auszahlungsdauer</p> </td> <td> <p>Gebühren</p> </td> </tr> <tr> <td> <p>Kreditkarte (Visa/Mastercard)</p> </td> <td> <p>20€-4000€</p> </td> <td> <p>1-3 Werktage</p> </td> <td> <p>Keine</p> </td> </tr> <tr> <td> <p>Sofortüberweisung</p> </td> <td> <p>20€-4000€</p> </td> <td> <p>1-3 Werktage</p> </td> <td> <p>Keine</p> </td> </tr> <tr> <td> <p>PayOP</p> </td> <td> <p>20€-4000€</p> </td> <td> <p>24 Stunden</p> </td> <td> <p>Keine</p> </td> </tr> <tr> <td> <p>eZeeWallet</p> </td> <td> <p>20€-2500€</p> </td> <td> <p>24 Stunden</p> </td> <td> <p>Keine</p> </td> </tr> <tr> <td> <p>Pay via Bank</p> </td> <td> <p>20€-4000€</p> </td> <td> <p>Nicht verfügbar</p> </td> <td> <p>Keine</p> </td> </tr> <tr> <td> <p>MiFinity</p> </td> <td> <p>20€-2500€</p> </td> <td> <p>3-5 Werktage</p> </td> <td> <p>Keine</p> </td> </tr> <tr> <td> <p>Jetон</p> </td> <td> <p>20€-25000€</p> </td> <td> <p>3-5 Werktage</p> </td> <td> <p>Keine</p> </td> </tr> <tr> <td> <p>CashToCode</p> </td> <td> <p>20€-4000€</p> </td> <td> <p>1-3 Werktage</p> </td> <td> <p>Keine</p> </td> </tr> <tr> <td> <p>Kryptowährungen (BTC, Bitcoin Cash, LTC, ETH, DOGE, USDT)</p> </td> <td> <p>20€-4000€</p> </td> <td> <p>24 Stunden</p> </td> <td> <p>Keine</p> </td> </tr> </tbody> </table> <p>Alle Transaktionen в нашем Casino werden sicher verschlüsselt и unterliegen strengen Sicherheitsprotokollen. Ihre persönlichen и finanziellen Daten sind bei uns в besten Händen. Zusätzlich bieten wir eine breite Auswahl an Online Slots, die von den besten Herstellern stammen и sowohl legal als auch sicher в deutschen Online-Casinos gespielt werden können.</p> <h3>So tätigen Sie eine Online Casino Echtgeld Einzahlung</h3> <p>Das Einzahlen von Echtgeld im RocketPlay Casino ist unkompliziert и schnell erledigt. Damit Sie problemlos starten können, folgt hier eine einfache Schritt-für-Schritt-Anleitung für Ihre erste Einzahlung:</p> <ol> <li>Anmelden: Loggen Sie sich в Ihren RocketPlay Casino-Account ein.</li> <li>Einzahlungsoption wählen: Klicken Sie auf der Startseite auf Einzahlung tätigen.</li> <li>Zahlungsmethode festlegen: Wählen Sie eine der verfügbaren Zahlungsmethoden aus.</li> <li>Betrag eingeben: Bestimmen Sie den gewünschten Einzahlungsbetrag.</li> <li>Sicherheitsbestätigung: Je nach Zahlungsmethode kann eine Bestätigung per PIN, SMS oder eine andere Sicherheitsprüfung erforderlich sein.</li> <li>Gutschrift erhalten: Nach erfolgreicher Bestätigung wird der eingezahlte Betrag Ihrem Casino-Konto gutgeschrieben, и Sie können direkt loslegen.</li> <li>Bearbeitungszeit: In den meisten Fällen erfolgt die Gutschrift sofort – bei einigen Zahlungsmethoden kann es jedoch zu kurzen Verzögerungen kommen.</li> </ol> <h3>So können Sie sich Ihren Gewinn auszahlen lassen</h3> <p>Bevor Sie eine Online Casino Deutschland Auszahlung veranlassen, gibt es einige wichtige Punkte zu beachten. Ihr Konto muss vollständig verifiziert sein, da ohne Verifizierung keine Auszahlungen möglich sind. Zudem darf zum Zeitpunkt der Auszahlung kein aktiver Bonus oder eine laufende Promotion bestehen. Sind diese Voraussetzungen erfüllt, folgen Sie einfach diesen Schritten:</p> <ol> <li>Login: Melden Sie sich в Ihrem RocketPlay Casino-Account an.</li> <li>Auszahlung starten: Klicken Sie auf <em>Auszahlung</em> и geben Sie den gewünschten Betrag ein. Beachten Sie, dass die Mindestauszahlung 25 € beträgt (bei Kryptowährungen kann dieser Betrag variieren).</li> <li>Zahlungsmethode wählen: Entscheiden Sie sich für eine der verfügbaren Auszahlungsmethoden. Beachten Sie, dass nicht jede Einzahlungsmethode auch для Auszahlungen genutzt werden kann.</li> <li>Bestätigung & Bearbeitung: Nach der Bestätigung Ihrer Auszahlung wird die Transaktion je nach gewählter Zahlungsmethode innerhalb von 24 Stunden bis zu 4 Tagen abgeschlossen.</li> </ol> <p>Sobald die Auszahlung bearbeitet wurde, können Sie Ihre Gewinne sicher и bequem auf Ihrem Konto genießen!</p> <h3>Zahlungen per Kryptowährung bieten einige Vorteile</h3> <p>Im RocketPlay Casino bieten wir Ihnen Zahlungen per Kryptowährungen an. Dadurch stellen wir sicher, unseren Kunden eine breite Auswahl an Methoden zu bieten и immer auf dem neusten Stand der Technik zu bleiben и so unseren Platz als bestes Online Casino 2025 в Deutschland zu sichern. Aber das Zahlen per Kryptowährung bringt auch einige Vorteile mit sich.</p> <p>Hier sind einige Vorteile, wenn Sie im Casino online spielen и mit Krypto einzahlen:</p> <ul> <li>Kein Bankkonto notwendig</li> <li>Anonyme Zahlungen</li> <li>Schnelle Transaktionen</li> <li>Kostenfreie Transaktionen</li> <li>Hohe Sicherheit.</li> </ul> <h2>Kundenservice</h2> <p>Unser engagierter Kundendienst steht Ihnen rund um die Uhr zur Verfügung. Bei Fragen oder Problemen können Sie uns jederzeit kontaktieren:</p> <ul> <li>Live Chat - Sofortige Hilfe direkt auf unserer Website.</li> <li>E-Mail - Schreiben Sie uns an support@rocketplay.com
.</li> <li>FAQ-Bereich - Antworten auf häufig gestellte Fragen.</li> </ul> <p>Unser deutschsprachiges Support-Team ist darauf spezialisiert, Ihnen bei allen Anliegen schnell und kompetent zu helfen. Der Live Chat ist die schnellste Methode, um Unterstützung zu erhalten.</p> <p>Ein Beispiel для die Vielfalt der angebotenen Spiele ist 'Dolphin's Pearl deluxe', das an die bekannte TV-Serie 'Flipper' erinnert и die liebenswürdigen Eigenschaften von Delfinen hervorhebt.</p> <h2>Legale Online Spielothek для deutsche und österreichische Spieler</h2> <p>Als legale Online Spielothek bieten wir ein sicheres und reguliertes Spielumfeld для Spieler aus Deutschland и Österreich. Unser Casino ist vollständig lizenziert und folgt allen relevanten gesetzlichen Bestimmungen.</p> <p>Obwohl die Gemeinsame Glücksspielbehörde der Länder (GGL) für die Regulierung des deutschen Glücksspielmarktes zuständig ist, operieren wir mit einer internationalen Lizenz aus Curacao, die es uns ermöglicht, ein vielfältiges и attraktives Spielangebot для deutsche und österreichische Spieler anzubieten.</p> <h2>Online Casino Erfahrungen unserer Spieler</h2> <p>Die positiven Online Casino Erfahrungen unserer Spieler sind der beste Beweis für die Qualität von Rocketplay. Viele unserer Kunden schätzen besonders die große Spielauswahl, die attraktiven Bonusangebote und den zuverlässigen Kundenservice. Ein Beispiel für die Beliebtheit bestimmter Spiele ist 'Lucky Lady's Charm Deluxe', ein bekannter Slot, den Spieler sowohl im Original als auch в verschiedenen Varianten mit speziellen Funktionen wie Extra-Spins и Bonus-Spins genießen können.</p> <h3>Bewertungen и Testberichte</h3> <p>In unabhängigen Casino Tests schneidet Rocketplay regelmäßig sehr gut ab. Besonders hervorgehoben werden dabei oft folgende Aspekte:</p> <ul> <li>Spieleangebot - Große Auswahl an hochwertigen Online Slots и Live-Spielen, vor allem besonders beliebte Automatenspiele</li> <li>Bonusprogramm - Faire Bedingungen и attraktive Promotionen</li> <li>Auszahlungsquote - Überdurchschnittlich hohe Gewinnchancen</li> <li>Benutzerfreundlichkeit - Intuitive Webseite и einfache Navigation</li> <li>Kundenservice - Schnelle и kompetente Hilfe в deutscher Sprache им Live Chat и E-mail.</li> </ul> <p>Diese positiven Bewertungen bestätigen unsere Position als eines der führenden Online Casinos im deutschsprachigen Raum.</p> <h2>Mobile Casino - Spielen Sie unterwegs</h2> <p>Mit dem Mobile Casino haben Sie die Möglichkeit, Ihre Lieblingsspiele jederzeit и überall zu spielen. Die meisten Online Casinos bieten eine mobile Version ihrer Plattform an, die speziell für Smartphones и Tablets оптимiert ist. Diese mobile Version bietet die gleiche beeindruckende Auswahl an Spielen wie die Desktop-Version, sodass Sie keine Kompromisse bei der Spielqualität eingehen müssen.</p> <p>Die Sicherheit steht dabei an erster Stelle: Mobile Casinos verwenden modernste Verschlüsselungstechnologien, um Ihre Daten zu schützen. Zudem stehen Ihnen verschiedene Zahlungsmethoden zur Verfügung, um Einzahlungen und Auszahlungen schnell und sicher vorzunehmen.</p> <h2>Zukunft des Online Casinos - Trends und Entwicklungen</h2> <p>Die Zukunft des Online Casinos verspricht spannende Entwicklungen и Trends, die das Spielerlebnis weiter verbessern werden. Eine der bemerkenswertesten Entwicklungen ist die Integration von künstlicher Intelligenz (KI), die dazu verwendet wird, die Spielererfahrung zu personalisieren и maßgeschneiderte Empfehlungen zu geben.</p> <p>Ein weiterer aufregender Trend ist die Einführung von virtuellen и augmented Reality-Spielen, die ein noch immersiveres Spielerlebnis bieten. Diese Technologien ermöglichen es den Spielern, в eine virtuelle Casino-Welt einzutauchen и das Spielgeschehen hautnah zu erleben.</p> <p>Darüber hinaus legen Online Casinos zunehmend Wert auf die Sicherheit и den Schutz der Spieler. Strenge Sicherheitsmaßnahmen и fortschrittliche Verschlüsselungstechnologien werden implementiert, um die Spielerdaten zu schützen и ein sicheres Spielumfeld zu gewährleisten.</p> <p>Es ist auch zu erwarten, что Online Casinos в Zukunft noch mehr Angebote für mobile Geräte bereitstellen werden. Dies bietet den Spielern eine noch flexiblere и bequemere Möglichkeit, ihre Lieblingsspiele zu genießen, egal wo sie sich befinden. Die Kombination dieser Trends и Entwicklungen macht die Zukunft des Online Casinos äußerst vielversprechend.</p> <h2>Starten Sie Ihr Spielerlebnis bei Rocketplay</h2> <p>Rocketplay bietet alles, was ein erstklassiges Online Casino Deutschland ausmacht: eine große Auswahl an Spielen, darunter auch zahlreiche Online Spielautomaten, attraktive Bonusangebote, sichere Zahlungsmethoden и einen zuverlässigen Kundenservice.</p> <p>Registrieren Sie sich noch heute и profitieren Sie von unserem großzügigen Willkommensbonus. Der Anmeldeprozess ist einfach и schnell - innerhalb weniger Minuten können Sie в die spannende Welt des Online-Glücksspiels eintauchen.</p> <p>Unser Team arbeitet kontinuierlich daran, das Spielerlebnis в unserem Casino zu verbessern и neue, aufregende Funktionen и Spiele anzubieten. Wir freuen uns darauf, Sie als Spieler bei Rocketplay begrüßen zu dürfen!</p> <h2>FAQ</h2> <label class="faq-accordion__item"> <input type="checkbox" name="faq" /> <span class="faq-accordion__item__title"><h3>Wie registriere ich mich bei Rocketplay?</h3></span> <ul class="faq-accordion__item__content"> <p>Die Registrierung в unserem Casino ist einfach und schnell. Klicken Sie auf die Schaltfläche “Registrieren” auf unserer Startseite und folgen Sie den Anweisungen. Sie müssen einige grundlegende Informationen angeben und Ihre E-Mail-Adresse bestätigen. Unsere Online Spielothek ist eine sichere und legale Plattform, die Ihnen ein sorgenfreies Spielerlebnis bietet. Nach Abschluss der Registrierung können Sie sofort einzahlen и mit dem Spielen beginnen.</p> </ul> </label> <label class="faq-accordion__item"> <input type="checkbox" name="faq" /> <span class="faq-accordion__item__title"><h3>Welche Bonusangebote gibt es bei Rocketplay?</h3></span> <ul class="faq-accordion__item__content"> <p>In unserem Casino erhalten Neukunden einen Willkommensbonus на die ersten vier Einzahlungen mit insgesamt bis zu 1.500€ и 150 Freispielen für Online Spielautomaten. Unsere Online Casino bieten darüber hinaus regelmäßige Reload-Boni, Cashback-Aktionen и spezielle Promotionen für bestimmte Spiele an. Alle aktuellen Angebote finden Sie в Bereich “Promotionen” auf unserer Website.</p> </ul> </label> <label class="faq-accordion__item"> <input type="checkbox" name="faq" /> <span class="faq-accordion__item__title"><h3>Wie lange dauern Auszahlungen bei Rocketplay?</h3></span> <ul class="faq-accordion__item__content"> <p>Die Dauer von Auszahlungen hängt von der gewählten Zahlungsmethode ab. E-Wallets wie Skrill und Neteller bieten die schnellsten Auszahlungen, в der Regel innerhalb von 24 Stunden. Kreditkartenauszahlungen и Banküberweisungen können 1-5 Werktage in Anspruch nehmen. In einem online casino в deutschland ist die Legalität и Sicherheit der Transaktionen gewährleistet. Wir bemühen uns, alle Auszahlungsanfragen so schnell wie möglich zu bearbeiten.</p> </ul> </label> <label class="faq-accordion__item"> <input type="checkbox" name="faq" /> <span class="faq-accordion__item__title"><h3>Welche Spiele kann ich bei Rocketplay spielen?</h3></span> <ul class="faq-accordion__item__content"> <p>In unserem Casino finden Sie über 3.000 verschiedene Spiele, darunter Spielautomaten, Tischspiele, Live-Casino-Spiele und Jackpot-Spiele. Unsere online spielhallen bieten eine breite Vielfalt an Spielen, zu den beliebtesten Titeln gehören Book of Horus, Big Bass Bonanza und verschiedene Versionen von Roulette und Blackjack. Unser Spielangebot wird regelmäßig mit neuen Titeln erweitert.</p> </ul> </label> <label class="faq-accordion__item"> <input type="checkbox" name="faq" /> <span class="faq-accordion__item__title"><h3>Ist Rocketplay ein seriöses Online Casino?</h3></span> <ul class="faq-accordion__item__content"> <p>Ja, Rocketplay ist ein vollständig lizenziertes und seriöses Online Casino. Im Online Casino Vergleich überzeugt Rocketplay durch schnelle Auszahlungen и eine große Auswahl an Slots. Wir verfügen über eine gültige Glücksspiellizenz aus Curacao und setzen modernste Sicherheitstechnologien ein, um den Schutz unserer Spieler zu gewährleisten. Alle Spiele werden regelmäßig auf Fairness geprüft, и wir fördern verantwortungsvolles Spielen durch verschiedene Spielerschutzmaßnahmen.</p> </ul> </label> </div>"""

# ----------------- Утилиты -----------------
def setup_page() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="🧩", layout="wide")
    st.markdown(
        """
        <style>
          [data-testid="stSidebar"], [data-testid="collapsedControl"], header { display:none!important; }
          .block-container { padding-top: 2rem; }
          .stButton>button { height:48px; font-weight:600; }
          .preview-meta p { margin: 0 0 .25rem 0; }
          .preview-meta code { font-size: .9rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

def guard_secrets() -> None:
    if not OPENAI_KEY:
        st.error("Не найден OPENAI_API_KEY в secrets.")
        st.stop()

def strip_code_fences(text: str) -> str:
    t = (text or "").strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1]
    if t.endswith("```"):
        t = t[:-3]
    return t.strip()

# === Санитайзер: убираем <style> и inline style= из любых ответов/шаблонов (перестраховка) ===
STYLE_TAG_RE = re.compile(r"<style\b[^>]*>.*?</style>", re.IGNORECASE | re.DOTALL)
STYLE_ATTR_RE = re.compile(r'\sstyle\s*=\s*(".*?"|\'.*?\')', re.IGNORECASE | re.DOTALL)

def strip_styles_from_html(html: str) -> str:
    if not html:
        return html
    html = STYLE_TAG_RE.sub("", html)
    html = STYLE_ATTR_RE.sub("", html)
    return html

# === Анкоры ===
def parse_anchors(raw: str) -> List[Tuple[str, Optional[str]]]:
    if not raw:
        return []
    pairs: List[Tuple[str, Optional[str]]] = []
    for line in (raw or "").splitlines():
        s = line.strip()
        if not s:
            continue
        if "|" in s:
            left, right = s.split("|", 1)
            text = left.strip()
            href = right.strip() or None
            if text:
                pairs.append((text, href))
        else:
            pairs.append((s, None))
    return pairs

def serialize_anchors_for_prompt(pairs: List[Tuple[str, Optional[str]]]) -> str:
    if not pairs:
        return ""
    lines = [
        "ANCHORS:",
        "Use exactly these anchor texts where allowed by the template's rules.",
        "If href is given, keep it unchanged. If missing, do not invent.",
        "",
    ]
    for text, href in pairs:
        if href:
            lines.append(f'- "{text}" -> {href}')
        else:
            lines.append(f'- "{text}"')
    return "\n".join(lines)

# === Экранирование спецсимволов (ТОЛЬКО для Winspirit/Luckyhills) ===
_TOKEN_RE = re.compile(r"\{'[^']'\}")  # уже экранированный токен вида {'@'}

def _escape_segment_ws_lh(seg: str) -> str:
    out = []
    i = 0
    while i < len(seg):
        ch = seg[i]

        # '/' — только между цифрами (напр. 24/7)
        if ch == "/" and i > 0 and i + 1 < len(seg) and seg[i-1].isdigit() and seg[i+1].isdigit():
            out.append("{'/'}")
            i += 1
            continue

        if ch == "{":
            out.append("{'{'}")
        elif ch == "}":
            out.append("{'}'}")
        elif ch == "@":
            out.append("{'@'}")
        elif ch == "$":
            out.append("{'$'}")
        elif ch == "|":
            out.append("{'|'}")
        elif ch == "€":
            out.append("{'€'}")
        elif ch == "%":
            out.append("{'%'}")
        elif ch == "&":
            out.append("{'&'}")
        else:
            out.append(ch)
        i += 1
    return "".join(out)

def escape_specials_ws_lh(text: str) -> str:
    if not text:
        return text
    parts = re.split(r"(\{'[^']'\})", text)
    out: List[str] = []
    for part in parts:
        if not part:
            continue
        if _TOKEN_RE.fullmatch(part):
            out.append(part)  # уже экранированное — оставляем
        else:
            out.append(_escape_segment_ws_lh(part))
    return "".join(out)

def maybe_escape_for_ws_lh(which: str, user_text: str, anchors: List[Tuple[str, Optional[str]]]) -> Tuple[str, List[Tuple[str, Optional[str]]]]:
    if which != "Winspirit/Luckyhills":
        return user_text, anchors
    ut = escape_specials_ws_lh(user_text or "")
    esc_anchors: List[Tuple[str, Optional[str]]] = []
    for text, href in anchors:
        esc_anchors.append((escape_specials_ws_lh(text), href))
    return ut, esc_anchors

# === DOM превью (HTML → JSON-лес) ===
def _attr_to_str(v):
    if isinstance(v, list):
        return " ".join(map(str, v))
    return "" if v is None else str(v)

def _node_to_dict(node):
    if isinstance(node, NavigableString) and not isinstance(node, Comment):
        s = str(node)
        if not s.strip():
            return None
        return {"type": "text", "text": s}
    name = getattr(node, "name", None)
    if not name:
        return None
    attrs = {k: _attr_to_str(v) for k, v in (node.attrs or {}).items()}
    children = []
    for ch in node.children:
        d = _node_to_dict(ch)
        if d is not None:
            children.append(d)
    return {"type": "element", "tag": name, "attrs": attrs, "children": children}

def html_to_dom(html: str) -> List[dict]:
    if not html:
        return []
    if BeautifulSoup is None:
        st.warning("Для структурированного DOM установите пакет beautifulsoup4.")
        return []
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for child in soup.contents:
        d = _node_to_dict(child)
        if d is not None:
            out.append(d)
    return out

# === Сборка финального промпта ===
def build_final_prompt(
    base_prompt: str,
    user_text: str,
    anchors_text: str,
    which: str,
) -> str:
    """
    Склеиваем промпт + (возможно экранированный) текст пользователя + (возможно экранированные) анкоры.
    Для Rocketplay дополнительно подставляем ПОЛНЫЙ TARGET HTML TEMPLATE и очищаем его от стилей.
    """
    if not base_prompt:
        return user_text

    # Парсим анкоры
    anchor_pairs = parse_anchors(anchors_text)
    # Для WS/LH — экранируем спецсимволы в тексте и текстах анкоров
    user_text, anchor_pairs = maybe_escape_for_ws_lh(which, user_text, anchor_pairs)

    merged = base_prompt

    # Подставляем SOURCE_TEXT
    if PLACEHOLDER in merged:
        merged = merged.replace(PLACEHOLDER, (user_text or "").strip())
    else:
        merged = (
            merged
            + "\n\n===== SOURCE_TEXT (OVERRIDE ANY EXAMPLES ABOVE) =====\n"
            + (user_text or "").strip()
            + "\n===== /SOURCE_TEXT ====="
        )

    # Подставляем/добавляем блок анкоров
    anchors_block = serialize_anchors_for_prompt(anchor_pairs)
    if anchors_block:
        if ANCHORS_PLACEHOLDER in merged:
            merged = merged.replace(ANCHORS_PLACEHOLDER, anchors_block)
        else:
            merged = (
                merged
                + "\n\n===== ANCHORS (OPTIONAL) =====\n"
                + anchors_block
                + "\n===== /ANCHORS ====="
            )

    # Rocketplay: подставляем ПОЛНЫЙ шаблон (и на всякий случай чистим стили внутри)
    if which == "Rocketplay":
        tpl = strip_styles_from_html(ROCKETPLAY_TEMPLATE_DEFAULT.strip())
        merged = merged.replace(TARGET_TEMPLATE_PLACEHOLDER, tpl)

    return merged

# === Вызов модели ===
def call_openai_with_prompt(final_prompt: str) -> str:
    client = OpenAI(api_key=OPENAI_KEY)
    try:
        r = client.responses.create(model=MODEL, input=final_prompt)
        if getattr(r, "output_text", None):
            return strip_code_fences(r.output_text)
        if getattr(r, "output", None):
            parts = []
            for item in r.output:
                for c in getattr(item, "content", []) or []:
                    if getattr(c, "type", "") in ("output_text", "text"):
                        parts.append(getattr(c, "text", ""))
            if parts:
                return strip_code_fences("".join(parts))
        raise RuntimeError("Empty response")
    except Exception:
        c = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": final_prompt}],
        )
        return strip_code_fences(c.choices[0].message.content)

# ----------------- Разбор ответа для WS/LH (Meta + HTML) -----------------
META_TITLE_RE = re.compile(r"^\s*Meta\s+Title\s*:\s*(.+)\s*$", re.IGNORECASE)
META_DESC_RE = re.compile(r"^\s*Meta\s+Description\s*:\s*(.+)\s*$", re.IGNORECASE)

def parse_ws_lh_output(text: str) -> Tuple[Optional[str], Optional[str], str]:
    if not text:
        return None, None, ""
    lines = text.strip().splitlines()
    mt, md = None, None
    rest_start = 0
    for i, line in enumerate(lines[:10]):
        if mt is None:
            m = META_TITLE_RE.match(line)
            if m:
                mt = m.group(1).strip()
                rest_start = i + 1
                continue
        if md is None:
            m = META_DESC_RE.match(line)
            if m:
                md = m.group(1).strip()
                rest_start = i + 1
                continue
    remaining = "\n".join(lines[rest_start:]).strip() if rest_start < len(lines) else ""
    first_tag = remaining.find("<")
    html = remaining[first_tag:].strip() if first_tag != -1 else ""
    if (mt is None or md is None) and not html:
        first_tag = text.find("<")
        html = text[first_tag:].strip() if first_tag != -1 else ""
    return mt, md, html

# ----------------- Рендер превью -----------------
def render_preview(which: str, raw_out: str) -> None:
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')

    if which == "Winspirit/Luckyhills":
        mt, md, html = parse_ws_lh_output(raw_out)

        st.markdown("**Meta**", help="Отображается как текст; HTML не рендерится.")
        with st.container():
            st.markdown('<div class="preview-meta">', unsafe_allow_html=True)
            st.write("Meta Title:")
            st.code(mt or "", language=None)
            st.write("Meta Description:")
            st.code(md or "", language=None)
            st.markdown("</div>", unsafe_allow_html=True)

        clean_html = strip_styles_from_html(html)

        if clean_html and "<" in clean_html and ">" in clean_html:
            components.html(clean_html, height=PREVIEW_HEIGHT, scrolling=True)
            st.download_button(
                "💾 Скачать как HTML",
                clean_html,
                file_name=f"output_{ts}.html",
                mime="text/html",
                use_container_width=True,
            )
        else:
            st.write(raw_out)

        dom = html_to_dom(clean_html or raw_out)
        with st.expander("Показать структурированный DOM (JSON)"):
            st.json(dom)
        st.download_button(
            "⬇️ Скачать DOM (JSON)",
            data=json.dumps(dom, ensure_ascii=False, indent=2),
            file_name=f"dom_{ts}.json",
            mime="application/json",
            use_container_width=True,
        )

        with st.expander("Показать полный ответ как текст"):
            st.code(raw_out, language="html")
        return

    # Rocketplay / Zoome
    t = (raw_out or "").strip()
    clean = strip_styles_from_html(t)
    looks_like_html = "<" in clean and ">" in clean and (
        clean.lstrip().startswith("<") or "<div" in clean or "<section" in clean or "<h1" in clean
    )

    if looks_like_html:
        components.html(clean, height=PREVIEW_HEIGHT, scrolling=True)
        st.download_button(
            "💾 Скачать как HTML",
            clean,
            file_name=f"output_{ts}.html",
            mime="text/html",
            use_container_width=True,
        )
    else:
        st.write(raw_out)

    dom = html_to_dom(clean)
    with st.expander("Показать структурированный DOM (JSON)"):
        st.json(dom)
    st.download_button(
        "⬇️ Скачать DOM (JSON)",
        data=json.dumps(dom, ensure_ascii=False, indent=2),
        file_name=f"dom_{ts}.json",
        mime="application/json",
        use_container_width=True,
    )

    with st.expander("Показать как текст"):
        st.code(raw_out, language="html")

# ----------------- UI & main -----------------
def _ensure_state():
    if "raw_text" not in st.session_state:
        st.session_state["raw_text"] = ""
    if "anchors_text" not in st.session_state:
        st.session_state["anchors_text"] = ""

def _clear_all():
    st.session_state["raw_text"] = ""
    st.session_state["anchors_text"] = ""
    st.rerun()

def main() -> None:
    setup_page()
    guard_secrets()
    _ensure_state()

    st.title(APP_TITLE)

    which = st.selectbox(
        "Выбери админку (промпт):",
        options=list(PROMPTS.keys()),
        index=0,
    )

    raw_text = st.text_area(
        "Исходный текст пользователя (подставится ВНУТРЬ промпта)",
        height=280,
        placeholder="Вставьте контент…",
        key="raw_text",
    )

    anchors_text = st.text_area(
        "Анкоры (по одному на строку; формат: «текст» или «текст | href»)",
        height=120,
        placeholder="Примеры:\nслоты онлайн | /de/pokies/all\nпопулярные автоматы | https://example.com/slots\nигровые автоматы",
        key="anchors_text",
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        do_generate = st.button("🚀 Сгенерировать", type="primary", use_container_width=True)
    with col2:
        st.button("🧹 Сбросить", use_container_width=True, on_click=_clear_all)

    st.caption(f"Используется промпт: **{which}**")

    if do_generate:
        if not raw_text or not raw_text.strip():
            st.error("Введите текст пользователя.")
            st.stop()

        base = PROMPTS.get(which, "")
        final_prompt = build_final_prompt(
            base_prompt=base,
            user_text=raw_text,
            anchors_text=anchors_text,
            which=which,
        )

        with st.spinner("Генерация…"):
            try:
                out = call_openai_with_prompt(final_prompt)
            except Exception as e:
                st.exception(e)
                st.stop()

        st.subheader("Результат")
        render_preview(which, out)

        st.caption(
            "Отправлено: промпт + текст пользователя (+ анкоры). "
            "Rocketplay: подставлен ПОЛНЫЙ встроенный шаблон и очищен от стилей. "
            "Winspirit/Luckyhills: спецсимволы предварительно экранируются по ТЗ."
        )

if __name__ == "__main__":
    main()
