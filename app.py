# -*- coding: utf-8 -*-
"""
Три админки — три промпта (захардкожены). API-ключ берём из st.secrets.
Мы отправляем ВМЕСТЕ и промпт, и строгий пример, и текст юзера —
через единый input (Responses API) либо чатовый фолбэк.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, Tuple

import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI

APP_TITLE = "🧩 HTML Transformer — 3 админки, промпты в коде"

# === Обязательный секрет ===
OPENAI_KEY: str = st.secrets.get("OPENAI_API_KEY", "")

# === Модель/превью ===
MODEL: str = os.getenv("HTML_TRANSFORMER_MODEL", "gpt-4.1-mini")
PREVIEW_HEIGHT: int = int(os.getenv("HTML_PREVIEW_HEIGHT", "1200"))

# Фраза-плейсхолдер, которую надо заменить текстом юзера
PLACEHOLDER = "Тут должен быть текст который вставил юзер"

# ---------- ВСТАВЬ СВОИ ПРОМПТЫ НИЖЕ ----------
# 1) Админка #1
HTML_PROMPT: str = r"""You are a rigorous HTML transformer. Output ONLY one HTML block. No explanations, no code fences. The first character must be “<” and the last must be “>”. It must start with <div class="markup-seo-page"> and end with </div>. Keep the TARGET HTML TEMPLATE structure 100% identical (same <style>, order, attributes). Enforce exact counts: 7 <a> with unchanged href, 1 <em> same position, 3 tables with row counts [6,3,10], 5 FAQ blocks with the exact schema. Replace ONLY inner text from RAW CONTENT. If overflow, condense with commas/semicolons. Do not invent. Do NOT escape special characters; keep all visible text exactly as in RAW CONTENT. Use straight quotes. [RAW CONTENT] Тут должен быть текст который вставил юзер [TARGET HTML TEMPLATE] <div class="markup-seo-page"> <style> .markup-seo-page { table { width: 100%; border-collapse: collapse; } td { border: 2px solid gray; padding: 8px; text-align: left; } ol { list-style-type: decimal; } .fe-button { color: var(--color-button-text-primary); text-decoration: none; } @media screen and (max-width: 600px) { td { border-width: 1px; padding: 4px; font-size: 11px; } } .seo-container { justify-items: stretch; } } </style> <h1>Rocketplay Online Casino Deutschland - Die beste Adresse für Spieler aus Deutschland und Österreich</h1> <p>Willkommen im Rocketplay Casino - dem führenden Online Casino Deutschland für Spieler aus Deutschland und Österreich! In unserem Casino Rocketplay erwarten Sie hochwertige Spiele, attraktive Boni und ein sicheres Spielerlebnis rund um die Uhr. Entdecken Sie jetzt die Welt des Premium-Glücksspiels!</p> <h2>Einführung in das Online Casino</h2> <p>Das Online Casino ist eine moderne Plattform, die es Spielern ermöglicht, eine Vielzahl von Glücksspielen bequem von zu Hause aus oder unterwegs zu genießen. In einem Online Casino können Sie beliebte Spiele wie Slots, Roulette, Blackjack und Poker spielen. Diese Spiele stammen von renommierten Anbietern wie Evolution, Play'N GO, Hacksaw Gaming und Pragmatic Play, die für ihre hochwertigen und unterhaltsamen Spiele bekannt sind.</p> <p>Spieler können auf diese Spiele über das Internet zugreifen und um Echtgeld spielen, was das Online Casino zu einer attraktiven Alternative zu traditionellen Spielhallen macht. In Deutschland sind Online Casinos legal und unterliegen den strengen Vorschriften des Glücksspielstaatsvertrags, der sicherstellt, dass alle Spiele fair und sicher ablaufen. Dies bietet den Spielern die Gewissheit, dass sie in einer regulierten und geschützten Umgebung spielen.</p> <h2>Warum unser Online Casino die beste Wahl ist</h2> <p>Als etabliertes Online Casino bietet Rocketplay ein erstklassiges Spielerlebnis für alle Spieler. Unser Casino zeichnet sich durch folgende Vorteile aus:</p> <ul> <li>Große Spieleauswahl - Über 3.000 hochwertige Casino Spiele von renommierten Anbietern</li> <li>Sichere Lizenz - Vollständig lizenziert durch Curacao</li> <li>Attraktive Bonusangebote - Großzügige Willkommensboni und regelmäßige Promotionen</li> <li>Schnelle Auszahlungen - Erhalten Sie Ihre Gewinne sicher und zügig</li> <li>Mehrsprachiger Support - Kundendienst in deutscher Sprache rund um die Uhr verfügbar</li> </ul> <p>In unserem Online Casino finden Sie alles, was das Spielerherz begehrt - von klassischen Top Spielautomaten bis hin zu spannenden Live-Spielen mit echten Dealern. Egal ob Sie aus Deutschland oder Österreich zu uns kommen, wir garantieren ein sicheres und unterhaltsames Spielerlebnis.</p> <h2>Online Casino Deutschland - Die besten Spiele bei Rocketplay</h2> <p>In unserem Online Casino Deutschland haben wir eine sorgfältig kuratierte Auswahl an Spielen zusammengestellt, die speziell auf die Vorlieben deutscher und österreichischer Spieler abgestimmt ist. Unsere Spielhallen bieten eine beeindruckende Vielfalt an Unterhaltungsmöglichkeiten, darunter beliebte Automatenspiele wie 'Book of Ra Magic' von namhaften Herstellern wie Novomatic.</p> <h3>Populäre Spielautomaten in unserem Casino</h3> <p>In unseren Online Spielotheken finden Sie <a href="/de/pokies/all"> beste Spielautomaten für Spieler aus Deutschland und Österreich</a>. Von klassischen Frucht Spielautomaten bis hin zu modernen Videoslots mit aufregenden Bonusfunktionen - bei uns wird jeder Spieler fündig.</p> <p>Zu den beliebtesten Slots in unserem Casino zählen:</p> <table> <tbody> <tr> <td> <p>Top Spielautomaten</p> </td> <td> <p>Anbieter</p> </td> <td> <p>Besonderheiten</p> </td> </tr> <tr> <td> <p>Wings of Horus</p> </td> <td> <p>Hacksaw Gaming</p> </td> <td> <p>Expandierendes Symbol, Freispiele</p> </td> </tr> <tr> <td> <p>Big Bass Bonanza</p> </td> <td> <p>Pragmatic Play</p> </td> <td> <p>Fisch-Sammel-Funktion, Multiplikatoren</p> </td> </tr> <tr> <td> <p>Sweet Bonanza</p> </td> <td> <p>Pragmatic Play</p> </td> <td> <p>Tumble-Feature, Freispiele mit Multiplikatoren</p> </td> </tr> <tr> <td> <p>Book of Dead</p> </td> <td> <p>Play’n GO</p> </td> <td> <p>Freispiele mit erweiterndem Symbol</p> </td> </tr> <tr> <td> <p>John Hunter and the Tomb of the Scarab Queen</p> </td> <td> <p>Pragmatic Play</p> </td> <td> <p>Abenteuer-Thema, Freispiele</p> </td> </tr> </tbody> </table> <p>Für Spieler, die immer auf dem neuesten Stand bleiben möchten, bieten wir regelmäßig <a href="/de/pokies/new"> neue Spielautomaten für Spieler aus Deutschland und Österreich</a> an. So können Sie stets die aktuellsten Spielinnovationen entdecken und genießen.</p> <h3>Big Bass Bonanza und andere beliebte Slots</h3> <p>Big Bass Bonanza gehört zu den absoluten Favoriten in unserem Online Casino. Dieser unterhaltsame Angel-Slot begeistert durch sein einzigartiges Spielprinzip und die Chance auf große Gewinne. Das Spiel bietet spannende Freispiele mit Multiplikatoren und die Möglichkeit, zusätzliche Fisch-Symbole zu sammeln.</p> <p>Ein weiteres Beispiel für die Vielfalt unserer angebotenen Slots ist 'Diamond Link: Mighty Elephant', das durch seine aufregenden Features und Themen überzeugt. Die Big Bass Serie hat sich aufgrund ihrer eingängigen Spielmechanik und des amüsanten Themas zu einem echten Hit entwickelt. Spieler aus Deutschland und Österreich schätzen besonders die faire Auszahlungsquote und die regelmäßigen Gewinnchancen.</p> <h3>Spielautomaten mit hoher Volatilität für risikobereite Spieler</h3> <p>Für Spieler, die bereit sind, ein höheres Risiko einzugehen, bieten wir <a href="/de/pokies/high-volatility"> Spielautomaten mit hoher Volatilität</a> an. Diese Spiele bieten die Chance auf besonders große Gewinne, auch wenn diese seltener auftreten als bei Online Slots mit niedrigerer Volatilität.</p> <p>Hochvolatile Slots sind ideal für geduldige Spieler, die auf den großen Gewinn warten können. Ein Beispiel hierfür ist 'Gates of Olympus', ein göttlicher Online Slot, der außergewöhnliche Themen, hohe Gewinnmöglichkeiten und Freispiele bietet. In unserem Casino finden Sie eine große Auswahl an diesen spannenden Spielen, die für den besonderen Nervenkitzel sorgen.</p> <h2>Online Spielotheken Vergleich - Darum überzeugt Rocketplay</h2> <p>Im Vergleich zu anderen Online Spielotheken hebt sich unser Casino Rocketplay durch zahlreiche Vorteile ab. Ein umfassender Online Casino Vergleich zeigt, dass wir durch schnelle Auszahlungen und eine große Auswahl an Online Slots überzeugen. Wir haben uns als eine der führenden Online Spielhallen im deutschsprachigen Raum etabliert und bieten ein Spielerlebnis der Extraklasse. Unsere Vorteile im Überblick:</p> <ol> <li>Umfangreiche Spieleauswahl - Über 3.000 Spiele von mehr als 40 Anbietern</li> <li>Attraktive Bonusangebote - Regelmäßige Promotionen und ein großzügiges VIP-Programm</li> <li>Sichere Zahlungsmethoden - Schnelle Ein- und Auszahlungen mit verschiedenen Optionen</li> <li>Hervorragender Kundendienst - Support rund um die Uhr in deutscher Sprache</li> <li>Optimierte mobile Version - Spielen Sie unterwegs auf Ihrem Smartphone oder Tablet</li> <li>Sicherheit und Legalität - Unsere Plattform steht unter der Aufsicht der Gemeinsamen Glücksspielbehörde der Länder, die für die Überwachung und Lizenzierung von Online-Spielotheken in Deutschland zuständig ist. Dies garantiert ein sicheres und legales Spielumfeld.</li> </ol> <p>Positive Casino Tests bestätigen regelmäßig die Qualität unseres Angebots. In unabhängigen Online Casino Tests schneidet Rocketplay regelmäßig als eines der Top Online Casinos für deutsche und österreichische Spieler ab.</p> <h3>Online Casino Seiten im Vergleich</h3> <p>Im umfangreichen Markt der Online Casino Seiten kann es schwierig sein, den Überblick zu behalten. Rocketplay sticht durch sein ausgewogenes Angebot und die Fokussierung auf die Bedürfnisse deutschsprachiger Spieler hervor.</p> <p>Unsere Casino Seiten wurden speziell für Spieler aus Deutschland und Österreich optimiert. Die Benutzeroberfläche ist intuitiv gestaltet und ermöglicht einen einfachen Zugang zu allen Bereichen unseres Casinos. Besonders wichtig ist uns die Sicherheit und Legalität der Einzahlungen, damit Ihr online casino geld stets geschützt ist und Sie sich keine Sorgen um die Rückforderung machen müssen.</p> <h3>Internet Casinos und ihre Besonderheiten</h3> <p>Online Casinos haben in den letzten Jahren stark an Beliebtheit gewonnen. Als modernes und innovatives Casino setzen wir bei Rocketplay auf die neuesten Technologien, um ein optimales Spielerlebnis zu gewährleisten.</p> <p>Unsere Online Spielbank ist eine sichere und legale Plattform, die den strengen gesetzlichen Vorgaben entspricht und Schutzmaßnahmen für die Daten der Spieler implementiert hat. Im Gegensatz zu landbasierten Spielhallen bietet unser Online Casino den Vorteil, dass Sie rund um die Uhr und von überall aus spielen können. Zudem profitieren Sie von einer deutlich größeren Spielauswahl und attraktiveren Bonusangeboten.</p> <h2>Freispiele und Boni in unserem Casino</h2> <p>Ein besonderes Highlight in unserem Online Casino sind die attraktiven Freispiele und Bonusangebote. Als neuer Spieler profitieren Sie von einem großzügigen Willkommensbonus, während treue Kunden regelmäßig mit Reload-Boni, Freispielen und der Chance auf cash-Gewinne belohnt werden.</p> <h3>Willkommensbonus для Neukunden</h3> <p>Als Neukunde in unserem Casino Rocketplay erhalten Sie einen attraktiven Willkommensbonus:</p> <table> <tbody> <tr> <td> <p>Einzahlung</p> </td> <td> <p>Bonus</p> </td> <td> <p>Freispiele</p> </td> <td> <p>Umsatzbedingungen</p> </td> </tr> <tr> <td> <p>1. Einzahlung</p> </td> <td> <p>100% bis zu 1000€</p> </td> <td> <p>100 Freispiele</p> </td> <td> <p>40х Bonus</p> </td> </tr> <tr> <td> <p>2. Einzahlung</p> </td> <td> <p>200% bis zu 1000€</p> </td> <td> <p>–</p> </td> <td> <p>40x Bonus</p> </td> </tr> </tbody> </table> <p>Mit diesem Bonuspaket können Sie Ihr Startguthaben erheblich erhöhen und haben die Möglichkeit, unser umfangreiches Spielangebot ausgiebig zu erkunden. Zusätzlich bieten unsere premium mitgliedschaften Zugang zu den höchsten Auszahlungsquoten und exklusiven Boni, die Ihr Spielerlebnis weiter aufwerten.</p> <h3>Gratis Freispiele und regelmäßige Promotionen</h3> <p>Neben dem Willkommensbonus bieten wir regelmäßig Gratis Freispiele und andere Promotionen an. Diese Aktionen werden wöchentlich aktualisiert и bieten immer neue Möglichkeiten, von zusätzlichen Vorteilen zu profitieren und dabei zu gewinnen.</p> <p>Unsere Freispiele können bei ausgewählten Spielautomaten eingesetzt werden und bieten die Chance на echte Gewinne ohne eigenen Einsatz. Die genauen Bedingungen finden Sie jeweils in der Beschreibung der Aktion.</p> <h3>Spielothek Bonus für treue Spieler</h3> <p>Unser Spielothek Bonus für Stammkunden umfasst regelmäßige Reload-Boni, Cashback-Aktionen und exklusive Turniere. Je aktiver Sie in unserem Casino spielen, desto mehr Vorteile genießen Sie.</p> <p>Ein besonderes Highlight ist unser VIP-Programm mit verschiedenen Stufen und exklusiven Vorteilen:</p> <ul> <li>Bronze - 5% wöchentlicher Cashback, schnellere Auszahlungen</li> <li>Silber - 7% wöchentlicher Cashback, persönlicher Account Manager</li> <li>Gold - 10% wöchentlicher Cashback, erhöhte Einzahlungs- und Auszahlungslimits</li> <li>Platin - 15% wöchentlicher Cashback, exklusive Boni und Promotionen</li> <li>Diamond - 20% wöchentlicher Cashback, VIP-Events und individuelle Angebote</li> </ul> <p>Ein weiteres Beispiel für attraktive Gewinnmöglichkeiten ist unser 'Cash Connection' Jackpot-Spiel, bei dem feste Jackpot-Gewinne auf Sie warten.</p> <p>Die Premium Mitgliedschaft in unserem VIP-Club bietet zusätzliche Vorteile wie persönliche Betreuung, höhere Limits und exklusive Boni mit Freispiele, die auf Ihre individuellen Vorlieben abgestimmt sind.</p> <h2>Online Casino in Deutschland - Sicherheit und Seriosität</h2> <p>Als Online Casino in Deutschland legen wir größten Wert auf Sicherheit und Seriosität. Rocketplay verfügt über eine gültige Glücksspiellizenz aus Curacao, die strenge Anforderungen an den Spielerschutz und die Fairness der angebotenen Spiele stellt. Online Spielbanken sind sichere und legale Plattformen, die speziell optimierte Spiele von führenden Software-Herstellern anbieten.</p> <h3>Sicheres Spielen bei Rocketplay</h3> <p>Die Sicherheit unserer Spieler hat für uns oberste Priorität. Wir setzen modernste SSL-Verschlüsselungstechnologie ein, um alle Daten und Transaktionen zu schützen. Zudem arbeiten wir nur mit renommierten Zahlungsdienstleistern zusammen, die höchste Sicherheitsstandards garantieren.</p> <p>Alle Spiele in unserem Casino werden regelmäßig von unabhängigen Prüfinstituten auf Fairness getestet. So können Sie sicher sein, dass bei uns alles mit rechten Dingen zugeht und jeder Spieler die gleichen Chancen auf Gewinne hat.</p> <h3>Verantwortungsvolles Spielen</h3> <p>We fördern verantwortungsvolles Glück und bieten verschiedene Tools zur Spielkontrolle an:</p> <ul> <li>Einzahlungslimits</li> <li>Spielzeitbegrenzungen</li> <li>Selbstausschlussoptionen</li> <li>Realitätschecks während des Spiels</li> <li>Selbsteinschätzungstests</li> </ul> <p>Die Spielteilnahme in unserem Casino soll in erster Linie Spaß machen und der Unterhaltung dienen. Wir ermutigen alle Spieler, ihre Grenzen zu kennen und innerhalb dieser zu spielen.</p> <h2>Live Casino - Das authentische Casinoerlebnis</h2> <p>Für Spieler, die die Atmosphäre eines echten Casinos schätzen, bieten wir ein erstklassiges Live Casino. Здесь können Sie <a href="/de/live/all"> Spielen Sie Live-Casino mit echten Live-Dealern</a> und die authentische Casino-Atmosphäre von zu Hause aus genießen. Zusätzlich bieten wir eine breite Palette an Automatenspielen, darunter beliebte Titel wie 'Fancy Fruits' von Bally Wulff, die sowohl klassische als auch moderne Hits umfassen.</p> <h3>Live-Blackjack mit echten Dealern</h3> <p>Blackjack-Enthusiasten kommen в unserem Live-Bereich voll auf ihre Kosten. Bei uns können Sie <a href="/de/live/blackjack"> Live-Blackjack mit echtem Croupier для Spieler aus Deutschland und Österreich</a> an verschiedenen Tischen mit unterschiedlichen Einsatzlimits spielen.</p> <p>Unsere professionellen Dealer sorgen für ein authentisches Spielerlebnis und stehen Ihnen bei Fragen jederzeit zur Verfügung. Die hochwertige Übertragung in HD-Qualität und die interaktiven Funktionen machen das Spiel besonders unterhaltsam.</p> <h3>Online-Roulette Live erleben</h3> <p>Ein weiteres Highlight в unserem Live Casino ist Roulette. Sie können <a href="/de/live/roulette"> Spielen Sie Online-Roulette und Live-Roulette</a> in verschiedenen Varianten, darunter Europäisches, Amerikanisches und Französisches Roulette. Ein weiteres Beispiel für die Vielfalt der angebotenen Spiele ist 'Diamond Link: Mighty Sevens', ein beliebtes Jackpot-Spiel mit festen Jackpots und spannenden Gewinnmechaniken.</p> <p>Die Spannung, wenn die Kugel im Roulettekessel rollt, ist auch beim Online-Spiel zu spüren. Durch die Live-Übertragung und die Interaktion mit dem Dealer entsteht ein immersives Spielerlebnis, das dem einer echten Spielbank sehr nahe kommt.</p> <h3>Baccarat und weitere Live-Spiele</h3> <p>Komplettiert wird unser Live-Angebot durch <a href="/de/live/baccarat"> Spiele Baccarat-Spiele</a> und weitere klassische Casinospiele. Baccarat erfreut sich besonders bei erfahrenen Spielern großer Beliebtheit und bietet spannende Spielrunden mit echten Dealern.</p> <p>Neben diesen Klassikern finden Sie в unserem Live Casino auch innovative Game Shows und spezielle VIP-Tische для höhere Einsätze. So ist für jeden Geschmack und jedes Budget etwas dabei. Darüber hinaus bieten wir eine Vielzahl von Spielautomaten, darunter beliebte Titel wie 'Rich Wilde and the Book of Dead', die für ihre abenteuerlichen Themen und spannenden Spielmechaniken bekannt sind.</p> <h2>Schritt-für Schritt zum RocketPlay Casino Konto</h2> <p>Um Zugriff auf die Echtgeld Casino Spiele online zu erhalten, müssen Sie ein Konto erstellen. Die RocketPlay Casino Registrierung ist dabei innerhalb weniger Momente abgeschlossen. Befolgen Sie dazu einfach die folgenden Schritte: </p> <ol> <li>Webseite aufrufen: Besuchen Sie die offizielle RocketPlay Casino Webseite und klicken Sie auf „Registrieren“,</li> <li>Daten angeben: Sie werden nun gebeten, Daten zu Ihrer Person anzugeben. Dazu gehören Datum, Alter und auch Adresse. </li> <li>E-Mail-Bestätigung: Sie erhalten nun eine E-Mail. Klicken Sie dort auf den Link, um Ihr Konto zu bestätigen. </li> <li>Einzahlung tätigen: Nun können Sie Ihre erste Einzahlung tätigen, um die Echtgeld-Spiele ausprobieren zu können. </li> </ol> <p>Seien Sie sich jedoch bewusst, dass Sie vor Ihrer ersten RocketPlay Casino Auszahlung Ihre Identität verifizieren müssen. So gehen wir sicher, dass Sie wirklich die Person sind, für die Sie sich ausgeben. Laden Sie dazu eine Kopie Ihres Ausweises sowie einen Адресnachweis hoch. Das ermöglicht uns, Ihnen die sicherste und beste Online Casino Erfahrung zu ermöglichen. </p> <h2>Casino spielen bei Rocketplay - Zahlungsmethoden und Support</h2> <p>Casino spielen bei Rocketplay ist nicht nur unterhaltsam, sondern auch einfach und sicher. Wir bieten verschiedene Zahlungsmethoden an, die schnelle und sichere Transaktionen gewährleisten. Zahlungsoptionen im Überblick:</p> <table> <tbody> <tr> <td> <p>Zahlungsmethode</p> </td> <td> <p>Mindesteinzahlung</p> </td> <td> <p>Auszahlungsdauer</p> </td> <td> <p>Gebühren</p> </td> </tr> <tr> <td> <p>Kreditkarte (Visa/Mastercard)</p> </td> <td> <p>20€-4000€</p> </td> <td> <p>1-3 Werktage</p> </td> <td> <p>Keine</p> </td> </tr> <tr> <td> <p>Sofortüberweisung</p> </td> <td> <p>20€-4000€</p> </td> <td> <p>1-3 Werktage</p> </td> <td> <p>Keine</p> </td> </tr> <tr> <td> <p>PayOP</p> </td> <td> <p>20€-4000€</p> </td> <td> <p>24 Stunden</p> </td> <td> <p>Keine</p> </td> </tr> <tr> <td> <p>eZeeWallet</p> </td> <td> <p>20€-2500€</p> </td> <td> <p>24 Stunden</p> </td> <td> <p>Keine</p> </td> </tr> <tr> <td> <p>Pay via Bank</p> </td> <td> <p>20€-4000€</p> </td> <td> <p>Nicht verfügbar</p> </td> <td> <p>Keine</p> </td> </tr> <tr> <td> <p>MiFinity</p> </td> <td> <p>20€-2500€</p> </td> <td> <p>3-5 Werktage</p> </td> <td> <p>Keine</p> </td> </tr> <tr> <td> <p>Jeton</p> </td> <td> <p>20€-25000€</p> </td> <td> <p>3-5 Werktage</p> </td> <td> <p>Keine</p> </td> </tr> <tr> <td> <p>CashToCode</p> </td> <td> <p>20€-4000€</p> </td> <td> <p>1-3 Werktage</p> </td> <td> <p>Keine</p> </td> </tr> <tr> <td> <p>Kryptowährungen (BTC, Bitcoin Cash, LTC, ETH, DOGE, USDT)</p> </td> <td> <p>20€-4000€</p> </td> <td> <p>24 Stunden</p> </td> <td> <p>Keine</p> </td> </tr> </tbody> </table> <p>Alle Transaktionen в unserem Casino werden sicher verschlüsselt und unterliegen strengen Sicherheitsprotokollen. Ihre persönlichen und finanziellen Daten sind bei uns в besten Händen. Zusätzlich bieten wir eine breite Auswahl an Online Slots, die von den besten Herstellern stammen und sowohl legal als auch sicher in deutschen Online-Casinos gespielt werden können.</p> <h3>So tätigen Sie eine Online Casino Echtgeld Einzahlung</h3> <p>Das Einzahlen von Echtgeld im RocketPlay Casino ist unkompliziert und schnell erledigt. Damit Sie problemlos starten können, folgt hier eine einfache Schritt-für-Schritt-Anleitung für Ihre erste Einzahlung:</p> <ol> <li>Anmelden: Loggen Sie sich в Ihren RocketPlay Casino-Account ein.</li> <li>Einzahlungsoption wählen: Klicken Sie auf der Startseite auf Einzahlung tätigen.</li> <li>Zahlungsmethode festlegen: Wählen Sie eine der verfügbaren Zahlungsmethoden aus.</li> <li>Betrag eingeben: Bestimmen Sie den gewünschten Einzahlungsbetrag.</li> <li>Sicherheitsbestätigung: Je nach Zahlungsmethode kann eine Bestätigung per PIN, SMS oder eine andere Sicherheitsprüfung erforderlich sein.</li> <li>Gutschrift erhalten: Nach erfolgreicher Bestätigung wird der eingezahlte Betrag Ihrem Casino-Konto gutgeschrieben, und Sie können direkt loslegen.</li> <li>Bearbeitungszeit: In den meisten Fällen erfolgt die Gutschrift sofort – bei einigen Zahlungsmethoden kann es jedoch zu kurzen Verzögerungen kommen.</li> </ol> <h3>So können Sie sich Ihren Gewinn auszahlen lassen</h3> <p>Bevor Sie eine Online Casino Deutschland Auszahlung veranlassen, gibt es einige wichtige Punkte zu beachten. Ihr Konto muss vollständig verifiziert sein, da ohne Verifizierung keine Auszahlungen möglich sind. Zudem darf zum Zeitpunkt der Auszahlung kein aktiver Bonus oder eine laufende Promotion bestehen. Sind diese Voraussetzungen erfüllt, folgen Sie einfach diesen Schritten:</p> <ol> <li>Login: Melden Sie sich в Ihrem RocketPlay Casino-Account an.</li> <li>Auszahlung starten: Klicken Sie auf <em>Auszahlung</em> und geben Sie den gewünschten Betrag ein. Beachten Sie, dass die Mindestauszahlung 25 € beträgt (bei Kryptowährungen kann dieser Betrag variieren).</li> <li>Zahlungsmethode wählen: Entscheiden Sie sich für eine der verfügbaren Auszahlungsmethoden. Beachten Sie, dass nicht jede Einzahlungsmethode auch für Auszahlungen genutzt werden kann.</li> <li>Bestätigung & Bearbeitung: Nach der Bestätigung Ihrer Auszahlung wird die Transaktion je nach gewählter Zahlungsmethode innerhalb von 24 Stunden bis zu 4 Tagen abgeschlossen.</li> </ol> <p>Sobald die Auszahlung bearbeitet wurde, können Sie Ihre Gewinne sicher und bequem auf Ihrem Konto genießen!</p> <h3>Zahlungen per Kryptowährung bieten einige Vorteile</h3> <p>Im RocketPlay Casino bieten wir Ihnen Zahlungen per Kryptowährungen an. Dadurch stellen wir sicher, unseren Kunden eine breite Auswahl an Methoden zu bieten und immer auf dem neusten Stand der Technik zu bleiben und so unseren Platz als bestes Online Casino 2025 in Deutschland zu sichern. Aber das Zahlen per Kryptowährung bringt auch einige Vorteile mit sich.</p> <p>Hier sind einige Vorteile, wenn Sie im Casino online spielen und mit Krypto einzahlen:</p> <ul> <li>Kein Bankkonto notwendig</li> <li>Anonyme Zahlungen</li> <li>Schnelle Transaktionen</li> <li>Kostenfreie Transaktionen</li> <li>Hohe Sicherheit.</li> </ul> <h2>Kundenservice</h2> <p>Unser engagierter Kundendienst steht Ihnen rund um die Uhr zur Verfügung. Bei Fragen oder Problemen können Sie uns jederzeit kontaktieren:</p> <ul> <li>Live Chat - Sofortige Hilfe direkt auf unserer Website.</li> <li>E-Mail - Schreiben Sie uns an support@rocketplay.com
.</li> <li>FAQ-Bereich - Antworten auf häufig gestellte Fragen.</li> </ul> <p>Unser deutschsprachiges Support-Team ist darauf spezialisiert, Ihnen bei allen Anliegen schnell und kompetent zu helfen. Der Live Chat ist die schnellste Methode, um Unterstützung zu erhalten.</p> <p>Ein Beispiel для die Vielfalt der angebotenen Spiele ist 'Dolphin's Pearl deluxe', das an die bekannte TV-Serie 'Flipper' erinnert und die liebenswürdigen Eigenschaften von Delfinen hervorhebt.</p> <h2>Legale Online Spielothek für deutsche und österreichische Spieler</h2> <p>Als legale Online Spielothek bieten wir ein sicheres und reguliertes Spielumfeld für Spieler aus Deutschland und Österreich. Unser Casino ist vollständig lizenziert und folgt allen relevanten gesetzlichen Bestimmungen.</p> <p>Obwohl die Gemeinsame Glücksspielbehörde der Länder (GGL) für die Regulierung des deutschen Glücksspielmarktes zuständig ist, operieren wir mit einer internationalen Lizenz aus Curacao, die es uns ermöglicht, ein vielfältiges und attraktives Spielangebot для deutsche und österreichische Spieler anzubieten.</p> <h2>Online Casino Erfahrungen unserer Spieler</h2> <p>Die positiven Online Casino Erfahrungen unserer Spieler sind der beste Beweis für die Qualität von Rocketplay. Viele unserer Kunden schätzen besonders die große Spielauswahl, die attraktiven Bonusangebote und den zuverlässigen Kundenservice. Ein Beispiel für die Beliebtheit bestimmter Spiele ist 'Lucky Lady's Charm Deluxe', ein bekannter Slot, den Spieler sowohl im Original als auch in verschiedenen Varianten mit speziellen Funktionen wie Extra-Spins und Bonus-Spins genießen können.</p> <h3>Bewertungen und Testberichte</h3> <p>In unabhängigen Casino Tests schneidet Rocketplay regelmäßig sehr gut ab. Besonders hervorgehoben werden dabei oft folgende Aspekte:</p> <ul> <li>Spieleangebot - Große Auswahl an hochwertigen Online Slots und Live-Spielen, vor allem besonders beliebte Automatenspiele</li> <li>Bonusprogramm - Faire Bedingungen und attraktive Promotionen</li> <li>Auszahlungsquote - Überdurchschnittlich hohe Gewinnchancen</li> <li>Benutzerfreundlichkeit - Intuitive Webseite und einfache Navigation</li> <li>Kundenservice - Schnelle und kompetente Hilfe in deutscher Sprache im Live Chat und E-mail.</li> </ul> <p>Diese positiven Bewertungen bestätigen unsere Position als eines der führenden Online Casinos im deutschsprachigen Raum.</p> <h2>Mobile Casino - Spielen Sie unterwegs</h2> <p>Mit dem Mobile Casino haben Sie die Möglichkeit, Ihre Lieblingsspiele jederzeit und überall zu spielen. Die meisten Online Casinos bieten eine mobile Version ihrer Plattform an, die speziell für Smartphones und Tablets оптимiert ist. Diese mobile Version bietet die gleiche beeindruckende Auswahl an Spielen wie die Desktop-Version, sodass Sie keine Kompromisse bei der Spielqualität eingehen müssen.</p> <p>Die Sicherheit steht dabei an erster Stelle: Mobile Casinos verwenden modernste Verschlüsselungstechnologien, um Ihre Daten zu schützen. Zudem stehen Ihnen verschiedene Zahlungsmethoden zur Verfügung, um Einzahlungen und Auszahlungen schnell und sicher vorzunehmen.</p> <h2>Zukunft des Online Casinos - Trends und Entwicklungen</h2> <p>Die Zukunft des Online Casinos verspricht spannende Entwicklungen und Trends, die das Spielerlebnis weiter verbessern werden. Eine der bemerkenswertesten Entwicklungen ist die Integration von künstlicher Intelligenz (KI), die dazu verwendet wird, die Spielererfahrung zu personalisieren und maßgeschneiderte Empfehlungen zu geben.</p> <p>Ein weiterer aufregender Trend ist die Einführung von virtuellen und augmented Reality-Spielen, die ein noch immersiveres Spielerlebnis bieten. Diese Technologien ermöglichen es den Spielern, in eine virtuelle Casino-Welt einzutauchen und das Spielgeschehen hautnah zu erleben.</p> <p>Darüber hinaus legen Online Casinos zunehmend Wert auf die Sicherheit und den Schutz der Spieler. Strenge Sicherheitsmaßnahmen und fortschrittliche Verschlüsselungstechnologien werden implementiert, um die Spielerdaten zu schützen und ein sicheres Spielumfeld zu gewährleisten.</p> <p>Es ist auch zu erwarten, dass Online Casinos in Zukunft noch mehr Angebote für mobile Geräte bereitstellen werden. Dies bietet den Spielern eine noch flexiblere und bequemere Möglichkeit, ihre Lieblingsspiele zu genießen, egal wo sie sich befinden. Die Kombination dieser Trends und Entwicklungen macht die Zukunft des Online Casinos äußerst vielversprechend.</p> <h2>Starten Sie Ihr Spielerlebnis bei Rocketplay</h2> <p>Rocketplay bietet alles, was ein erstklassiges Online Casino Deutschland ausmacht: eine große Auswahl an Spielen, darunter auch zahlreiche Online Spielautomaten, attraktive Bonusangebote, sichere Zahlungsmethoden und einen zuverlässigen Kundenservice.</p> <p>Registrieren Sie sich noch heute und profitieren Sie von unserem großzügigen Willkommensbonus. Der Anmeldeprozess ist einfach und schnell - innerhalb weniger Minuten können Sie in die spannende Welt des Online-Glücksspiels eintauchen.</p> <p>Unser Team arbeitet kontinuierlich daran, das Spielerlebnis в unserem Casino zu verbessern und neue, aufregende Funktionen und Spiele anzubieten. Wir freuen uns darauf, Sie als Spieler bei Rocketplay begrüßen zu dürfen!</p> <h2>FAQ</h2> <label class="faq-accordion__item"> <input type="checkbox" name="faq" /> <span class="faq-accordion__item__title"><h3>Wie registriere ich mich bei Rocketplay?</h3></span> <ul class="faq-accordion__item__content"> <p>Die Registrierung в unserem Casino ist einfach und schnell. Klicken Sie auf die Schaltfläche “Registrieren” auf unserer Startseite und folgen Sie den Anweisungen. Sie müssen einige grundlegende Informationen angeben und Ihre E-Mail-Adresse bestätigen. Unsere Online Spielothek ist eine sichere und legale Plattform, die Ihnen ein sorgenfreies Spielerlebnis bietet. Nach Abschluss der Registrierung können Sie sofort einzahlen und mit dem Spielen beginnen.</p> </ul> </label> <label class="faq-accordion__item"> <input type="checkbox" name="faq" /> <span class="faq-accordion__item__title"><h3>Welche Bonusangebote gibt es bei Rocketplay?</h3></span> <ul class="faq-accordion__item__content"> <p>In unserem Casino erhalten Neukunden einen Willkommensbonus auf die ersten vier Einzahlungen mit insgesamt bis zu 1.500€ und 150 Freispielen für Online Spielautomaten. Unsere Online Casino bieten darüber hinaus regelmäßige Reload-Boni, Cashback-Aktionen und spezielle Promotionen für bestimmte Spiele an. Alle aktuellen Angebote finden Sie im Bereich “Promotionen” auf unserer Website.</p> </ul> </label> <label class="faq-accordion__item"> <input type="checkbox" name="faq" /> <span class="faq-accordion__item__title"><h3>Wie lange dauern Auszahlungen bei Rocketplay?</h3></span> <ul class="faq-accordion__item__content"> <p>Die Dauer von Auszahlungen hängt von der gewählten Zahlungsmethode ab. E-Wallets wie Skrill und Neteller bieten die schnellsten Auszahlungen, in der Regel innerhalb von 24 Stunden. Kreditkartenauszahlungen und Banküberweisungen können 1-5 Werktage in Anspruch nehmen. In einem online casino in deutschland ist die Legalität und Sicherheit der Transaktionen gewährleistet. Wir bemühen uns, alle Auszahlungsanfragen so schnell wie möglich zu bearbeiten.</p> </ul> </label> <label class="faq-accordion__item"> <input type="checkbox" name="faq" /> <span class="faq-accordion__item__title"><h3>Welche Spiele kann ich bei Rocketplay spielen?</h3></span> <ul class="faq-accordion__item__content"> <p>In unserem Casino finden Sie über 3.000 verschiedene Spiele, darunter Spielautomaten, Tischspiele, Live-Casino-Spiele und Jackpot-Spiele. Unsere online spielhallen bieten eine breite Vielfalt an Spielen, zu den beliebtesten Titeln gehören Book of Horus, Big Bass Bonanza und verschiedene Versionen von Roulette und Blackjack. Unser Spielangebot wird regelmäßig mit neuen Titeln erweitert.</p> </ul> </label> <label class="faq-accordion__item"> <input type="checkbox" name="faq" /> <span class="faq-accordion__item__title"><h3>Ist Rocketplay ein seriöses Online Casino?</h3></span> <ul class="faq-accordion__item__content"> <p>Ja, Rocketplay ist ein vollständig lizenziertes und seriöses Online Casino. Im Online Casino Vergleich überzeugt Rocketplay durch schnelle Auszahlungen und eine große Auswahl an Slots. Wir verfügen über eine gültige Glücksspiellizenz aus Curacao und setzen modernste Sicherheitstechnologien ein, um den Schutz unserer Spieler zu gewährleisten. Alle Spiele werden regelmäßig auf Fairness geprüft, und wir fördern verantwortungsvolles Spielen durch verschiedene Spielerschutzmaßnahmen.</p> </ul> </label>
"""

# 2) Админка #2 (WinSpirit / LuckyHills) — ЖЁСТКИЙ конвертер, возвращает ровно заданный текст/HTML
HTML_PROMPT_WS_LH: str = r"""
You are a rigorous SEO HTML transformer.

OUTPUT FORMAT (strict):
1) Line 1: Meta Title: <title from RAW CONTENT (≤70 chars; if RAW has "Title:", reuse verbatim)>
2) Line 2: Meta Description: <description (140–160 chars; if RAW has "Description:", reuse verbatim)>
3) Immediately after line 2: ONE (1) HTML block ONLY. No other text before/after. No code fences. No explanations.

GLOBAL RULES:
- Keep the TARGET HTML TEMPLATE structure 100% identical (same tags, nesting, order, attributes, and element counts).
- Replace inner visible text nodes ONLY. Never add/remove/reorder elements.
- Keep EXACTLY 8 <a> tags with their hrefs UNCHANGED and in the SAME positions as in the template.
- Keep EXACTLY 2 <table> elements with TOTAL ROW COUNTS:
  • Table #1 = 3 rows total (1 header + 2 data)
  • Table #2 = 7 rows total (1 header + 6 data)
- Keep the number and order of <section>, <h1>, <h2>, <h3>, <ul>/<li>, <p> exactly as in the template.
- Language: match the MAJORITY language of RAW CONTENT consistently across the entire output.
- No fabrication: if a required value is missing, insert a single dash "-" in that place.
- If text is too long, condense with commas/semicolons; keep concise and on-topic.
- Do NOT escape visible characters from RAW CONTENT; keep HTML entities as-is (e.g., &uuml; stays &uuml;).
- Normalize brace-wrapped literals common in copied HTML: "{'%'}" → "%", "{'&'}" → "&".
- Whitespace constraints: the very first line must start with "Meta Title:"; the last character of the whole output must be the closing ">" of the last </section> tag.

META LINES:
- If RAW begins with lines "Title:" and "Description:", copy their values verbatim into Meta Title / Meta Description.
- Otherwise, synthesize both from RAW headlines/first paragraph ONLY (no inventions).

ANCHORS:
- You may change anchor INNER TEXTS using phrases supported by RAW CONTENT, but NEVER change their href attributes or positions. If no suitable text exists, use "-".

HEADINGS & PARAGRAPHS:
- Replace inner text of <h1>, <h2>, <h3>, <p>, <li> with concise content derived strictly from RAW CONTENT.
- If a sentence/section can’t be supported, place "-" (single dash) as content.

TABLE HANDLING (critical):
- RAW CONTENT may include 0, 1, or multiple HTML tables with any shapes; treat them as data sources.
- You must populate the TWO fixed TEMPLATE tables without altering their headers or structure.
- Selection for TEMPLATE Table #1 (4 columns, 2 data rows):
  • Prefer a source table listing “items” (e.g., slots/games/offers) with multiple attributes.
  • If multiple candidate tables exist, pick the most specific/recent one by order of appearance.
  • If NO source tables exist, derive rows from structured lists (<ul>/<ol>) or clearly itemized paragraphs.
- Mapping for TEMPLATE Table #1 cells:
  COL1 → compact main identifier (e.g., "<Item> – <Provider>" if both found; else the best available identifier)
  COL2 → short numeric/grade fact if present (e.g., "RTP 96.0%"); otherwise a concise spec/label
  COL3 → 1–2 key features joined by commas
  COL4 → short constraint/price/minimum if present; otherwise "-"
- Selection for TEMPLATE Table #2 (2 columns, 6 data rows):
  • Build rows from provider-like entities (vendors/brands). If a numeric count appears near the name (e.g., "88 games"), place it in "Games Available"; otherwise, "-".
  • If fewer than 6 providers are available, fill remaining rows with "-".
- Truncation & padding:
  • If a source table/list has more rows than needed, keep the first N by source order and drop the rest.
  • If fewer than needed, pad remaining rows with "-".
  • If a needed field is absent in a chosen row, write "-".
- Clean cell text: strip inner tags; join multiple source fragments with " – " or ", " as appropriate.

[RAW CONTENT]
<Вставь сюда любой исходный текст/HTML пользователя. Можно длинный — трансформер сам извлечёт факты, ужмёт таблицы и распределит контент по разделам шаблона.>

[TARGET HTML TEMPLATE]
Meta Title: Casino Bingo Online Australia - Lucky Hills Bingo Games Real Money
Meta Description: Play casino bingo online at Lucky Hills Australia. Enjoy bingo games, free bingo, mobile bingo with real money prizes. Join our bingo rooms today!
<h1>Casino Bingo Online at Lucky Hills Australia</h1>
<p>Welcome to Lucky Hills, where we bring you the ultimate casino bingo online experience for Australian players. At our casino Lucky Hills, we provide an exceptional collection of games that combine traditional fun with modern online gaming technology. Our platform offers players in Australia the perfect place to enjoy bingo and casino entertainment from the comfort of their own home.</p>
<section>
<h2>Online Bingo Experience at Our Casino</h2>
<p>We pride ourselves on offering an extensive range of online bingo games that cater to every player's preferences. Our bingo casino features titles from top-tier providers including Mascot Gaming, Betsoft, VoltEnt, Platipus, and Bgaming. Each game delivers authentic experience with modern twists and exciting features.</p>
<p>The variety of <a href="/">online casino for real money in Australia</a> gaming options makes Lucky Hills the perfect place for Australian players seeking quality entertainment.</p>
<h3>Popular Bingo Games</h3>
<p>Our collection includes various bingo games that guarantee hours of entertainment and chances to win real money. Here are some of our most popular titles that you can discover:</p>
<ul>
<li>Mayan Riches Bingo - Ancient treasures meet modern bingo fun</li>
<li>Wild Bingo - Classic bingo with wild multipliers</li>
<li>Extra Bingo - Enhanced gameplay with bonus features</li>
<li>Across Universe Keno - Space-themed keno adventure</li>
<li>Amaterasu Keno - Japanese-inspired keno experience</li>
<li>Plinko XY - Exciting ball-drop variant</li>
<li>Olympus Plinko - Mythological plinko adventure</li>
</ul>
</section>
<section>
<h2>Bingo Rooms and Gaming Environment</h2>
<p>Within our online bingo rooms, you are able to enjoy a wide array of variations. Every bingo room has something for you whether it’s about ticket prices, prize money or playing style, you choose. When enough players join the game, it recreates a community at large.</p>
<p>For those who enjoy table games, our <a href="/live/categories/roulette">online roulette in Australia</a> section provides additional excitement between sessions.</p>
<h3>Ball Bingo Variations</h3>
<p>We offer several ball bingo variations to keep the excitement fresh and ensure you never miss out on winning opportunities:</p>
<ul>
<li>90-Ball Bingo - Traditional format with one line, two lines, and full house prizes</li>
<li>75-Ball Bingo - American-style with certain pattern completions</li>
<li>30-Ball Bingo - Fast-paced mini for quick wins</li>
</ul>
<p>Each variation offers unique winning combinations and progressive jackpot opportunities that can result in substantial winnings.</p>
<h3>Bingo Cards and Bingo Tickets</h3>
<p>Our bingo tickets feature clear, easy-to-read bingo cards with automatically marked numbers. When the game starts, numbers are called automatically, and your cards are marked instantly. This system ensures you never miss a winning ticket or certain pattern completion.</p>
<p>Players can purchase multiple bingo tickets to increase their chances of winning, with each ticket offering the same chance of success. The ticket price varies depending on the game and potential prizes available.</p>
</section>
<section>
<h2>Mobile Bingo Games</h2>
<p>Australian players can enjoy our mobile bingo games on any device, anywhere. Our mobile platform provides the same quality experience as desktop gaming, with optimised interfaces for smartphones and tablets. Playing online has never been more convenient or accessible.</p>
<p>The mobile experience includes access to our <a href="/casino/categories/slots">online pokies for real money</a> collection, providing variety when you want a break from bingo.</p>
</section>
<section>
<h2>Welcome Bonus and Casino Bingo Promotions</h2>
<p>We offer generous welcome bonus packages for new Australian players joining our bingo online casino. Our current promotional structure includes exciting opportunities to boost your bankroll and extend your gameplay with additional cash and free spins.</p>
<h3>Welcome Bonus Package</h3>
<p>Our welcome bonus structure provides excellent value for new players looking to play bingo online:</p>
<table>
<tbody>
<tr>
<td><p>Deposit</p></td>
<td><p>Bonus</p></td>
<td><p>Free Spins</p></td>
<td><p>Minimum Deposit</p></td>
</tr>
<tr>
<td><p>First</p></td>
<td><p>100% Match</p></td>
<td><p>100 Free Spins</p></td>
<td><p>30 AUD</p></td>
</tr>
<tr>
<td><p>Second</p></td>
<td><p>200% Match</p></td>
<td><p>-</p></td>
<td><p>30 AUD</p></td>
</tr>
</tbody>
</table>
<h3>Bingo Bonus Casino Promotions</h3>
<p>We regularly run casino bingo promotions to keep the excitement alive for our loyal players. These promotions include cashback offers, free tickets, and special tournaments with substantial prize pools featuring progressive jackpot elements.</p>
<p>Current Promotions Include:</p>
<ul>
<li>No-deposit weekly cashback up to 5%</li>
<li>Wednesday free spins - up to 50 free spins</li>
<li>Sunday gifts with up to 30% bonus</li>
<li>Provider tournaments with prize pools exceeding 650,000 AUD</li>
</ul>
<p>Our <a href="/promotions/casino">deposit bonus casino</a> section provides full details about all available offers and their wagering requirements.</p>
</section>
<section>
<h2>Casino with Bingo - Progressive Jackpot Opportunities</h2>
<p>Many of our games feature progressive jackpot elements that grow with each game played. These jackpots can reach substantial amounts, providing life-changing win potential for lucky players. Our <a href="/casino/categories/jackpot">progressive jackpot slots online</a> section also complements the bingo experience perfectly.</p>
<p>The progressive jackpot system means that every bet contributes to growing prize pools, creating excitement and anticipation with each game. Winners can claim these substantial prizes when luck strikes.</p>
</section>
<section>
<h2>Game Providers and Quality</h2>
<p>We partner with established providers to ensure our games meet the highest standards. Our provider portfolio includes top developers who complete our gaming experience:</p>
<table>
<tbody>
<tr>
<td><p>Provider</p></td>
<td><p>Games Available</p></td>
</tr>
<tr><td><p>Mascot Gaming</p></td><td><p>87 games</p></td></tr>
<tr><td><p>NetGame</p></td><td><p>114 games</p></td></tr>
<tr><td><p>Playson</p></td><td><p>58 games</p></td></tr>
<tr><td><p>VoltEnt</p></td><td><p>253 games</p></td></tr>
<tr><td><p>Fugaso</p></td><td><p>60 games</p></td></tr>
<tr><td><p>Platipus</p></td><td><p>144 games</p></td></tr>
</tbody>
</table>
<p>And this is just the beginning of the list of providers on our platform. They make incredible pokies, live games, and much more.</p>
<h3>Game Quality and Features</h3>
<p>Each bingo game in our collection offers smooth gameplay, clear graphics, and fair random number generation. The games load quickly and run smoothly on all devices, ensuring consistent entertainment value and fun for every player.</p>
</section>
<section>
<h2>Deposit and Banking Options</h2>
<p>Australian players can easily fund their accounts using various secure deposit methods. Our minimum deposit requirement of 30 Australian dollars to receive the Welcome Bonus makes our games accessible to players with different budgets. The deposit process is straightforward and secure, allowing you to start playing within minutes.</p>
<p>Card games enthusiasts can also explore our <a href="/live/categories/poker">online poker in Australia for real money</a> tables for additional gaming variety.</p>
</section>
<section>
<h2>Online Bingo Casino Australia - Security and Licensing</h2>
<p>Lucky Hills operates as a licensed online bingo casino Australia, ensuring all games meet international standards for fairness and security. Your personal information and financial transactions are protected using advanced encryption technology, giving you peace of mind while you play.</p>
</section>
<section>
<h2>Classic Bingo and Traditional Formats</h2>
<p>For players who prefer traditional gameplay, our classic bingo selection offers authentic experiences that capture the essence of traditional bingo halls. These games feature familiar rules and straightforward gameplay that appeals to both newcomers and experienced players.</p>
</section>
<section>
<h2>Additional Gaming Options Beyond Bingo Online</h2>
<p>Beyond bingo online, our casino offers complementary gaming experiences. Players enjoy slots collections, <a href="/live">live casino online for real money</a> tables, and various other gaming options. This variety ensures you'll always find entertaining alternatives when you want a break from bingo.</p>
<p>For sophisticated gaming experiences, our <a href="/live/categories/baccara">baccarat online casino</a> tables provide elegant entertainment options.</p>
</section>
<section>
<h2>Bingo Casino Real Money Gaming Tips</h2>
<p>When you play bingo for real money, consider these helpful tips to enhance your bingo experience:</p>
<ul>
<li>Start with smaller ticket price games to understand the format</li>
<li>Take advantage of games to practice</li>
<li>Participate in chat to learn from other players</li>
<li>Manage your money responsibly with deposit limits</li>
<li>Look for games with better prizes to winnings ratios</li>
</ul>
</section>
<section>
<h2>Bingo for Money Online Casino - Getting Started</h2>
<p>Joining our bingo for money online casino community is simple and straightforward. The registration process takes just minutes, and you can start exploring our free bingo games immediately. Once you're ready to play for real money, our promotional offers provide excellent starting value.</p>
<p>The process to sign up involves just a few steps, and you'll quickly discover why our platform is the preferred choice for Australian players seeking quality bingo entertainment.</p>
</section>
<section>
<h2>Responsible Gaming Features</h2>
<p>We provide comprehensive responsible gaming tools to help players maintain control over their gaming activities. These include deposit limits, session time reminders, and self-exclusion options. Playing online should always remain fun and within your means.</p>
</section>
<section>
<h2>Online Bingo Promotions and Loyalty Rewards</h2>
<p>Our online bingo promotions extend beyond the welcome bonus to include ongoing rewards for loyal players. Regular tournaments, seasonal events, and special promotions ensure there's always something exciting happening at our casino.</p>
<p>Members can participate in provider tournaments like "Chasing the Gods" with 654,500 AUD prize pool and "Golden Sands" featuring 162,000 AUD in prizes. These events add extra excitement to regular gameplay.</p>
</section>
<section>
<h2>Understanding Wagering Requirements</h2>
<p>Each bonus has fair wagering requirements explained before claiming it. We are committed to being upfront, so we make all the bonus terms and conditions clear. If you know not to go for them, you won’t spend impulsively!</p>
</section>
"""



# 3) Админка #3 (Zoome)
HTML_PROMPT_ZOOME: str = r"""HTML_PROMPT_ZOOME = '''Ты — конвертер текста в фиксированный HTML-шаблон.
На вход ты получаешь только сырой текст (без HTML). На выходе ты обязан вернуть строго один HTML-документ, чья структура, порядок секций, количество тегов и их иерархия полностью совпадают с «ОПОРНЫМ ШАБЛОНОМ HTML».

Язык

Используй язык входного текста если англ значит англ и тд(не переводить).

Жёсткие правила

Никаких дополнительных секций/тегов/атрибутов. Разметка, порядок, количество <section>, <h1>…</h3>, <p>, <ul>, <li>, <table>, <tr>, <td> — идентичны шаблону.

Не менять, не удалять и не добавлять ссылки/href, названия игр, провайдеров, RTP, заголовки и структуру таблиц. Они — фиксированы и должны остаться неизменными.

Заполняй только текстовые узлы внутри уже существующих <p> и, где уместно, адаптируй упоминание бренда под входной текст (замени «Zoome» на бренд из входа). Новых тегов не добавлять.

Если во входном тексте нет данных — ставь нейтральные формулировки («—», «Детали уточняются.»), не меняя структуру.

Никаких комментариев/объяснений/Markdown. Только HTML.

Элементы списков и строки таблиц не удалять и не добавлять — заполняй описаниями из входа либо нейтрально.

Бренд подставляй везде, где в шаблоне «Zoome». Если бренд не найден — используй «—».

Извлечение данных

Бренд: первое упоминание названия казино/сайта во входе.

Вводные абзацы: сжато перефразуй преимущества/описание из входа.

Бонусы/промо: подставь цифры/условия из входа в соответствующие абзацы/списки; иначе — нейтральные заглушки.

Платежи/поддержка/ответственная игра: отрази факты из входа в соответствующих местах текста (без изменения структуры).

FAQ: переформулируй ответы по входу; при отсутствии — нейтральные ответы «—».

ОПОРНЫЙ ШАБЛОН HTML (начинается со следующей строки)

<section> <h1>Discover the World of Book Casino Games at Zoome</h1> <p>Welcome to Zoome Casino, where excitement meets opportunity in every spin of the wheel and every turn of a card. Our <a href="/">online casino Australia</a> is home to some of the most engaging book casino games available in Australia, designed to provide players with thrilling experiences, generous bonuses, and endless chances to win. Whether you&rsquo;re a fan of classic casino games like roulette, blackjack, and poker, or prefer innovative slots that transport you into mythological worlds and ancient lands, Zoome has something for everyone.</p> <p>The selection of titles in our library isn&rsquo;t just created to entertain&mdash;it&rsquo;s designed to bring real value to our customers. With trusted providers, a wide range of high-RTP releases, and secure casino gambling sessions, Zoome offers a safe environment where players can fully enjoy the action.</p> </section> <section> <h2>Overview of Book-Themed Casino Games at Zoome</h2> <p>At Zoome, we believe in diversity. Our catalogue combines the thrill of traditional casino gambling with modern innovation. Players can play everything from timeless table games such as roulette, blackjack, and craps, to immersive <a href="/games/slots">Aussie online pokies</a> and the ever-popular book series.</p> <p>What makes our gaming options stand out?</p> <ul> <li>High RTP percentages ensure fair pays and a chance to win big.</li> <li>A symbol-driven gameplay style that makes every round unique.</li> <li>Seamless compatibility with desktop and mobile devices.</li> <li>Bonuses and promotions that provide more value for both new and loyal players.</li> </ul> <p>The book games in particular hold a special place at Zoome. These titles are not just about spinning reels&mdash;they&rsquo;re about entering ancient temples, discovering hidden treasures, and unlocking mystical secrets. Every book symbol has the power to trigger free rounds, expanding symbols, or jackpot action, making them an essential part of the Zoome casino experience.</p> </section> <section> <h2>Table of Top Book Casino Games</h2> <p>Before diving deeper into bonuses and promotions, here&rsquo;s a look at some of the top-rated book slots you&rsquo;ll find at Zoome Casino. These are just a few highlights from our vast collection:</p> </section> <section> <table> <tbody> <tr> <td> <p>Game Title</p> </td> <td> <p>Provider</p> </td> <td> <p>RTP</p> </td> <td> <p>Key Features</p> </td> </tr> <tr> <td> <p>Book of Nibiru</p> </td> <td> <p>1spin4win</p> </td> <td> <p>96.1%</p> </td> <td> <p>Ancient Egypt theme, expanding symbols, free spins feature</p> </td> </tr> <tr> <td> <p>Book of Wild</p> </td> <td> <p>1spin4win</p> </td> <td> <p>95.8%</p> </td> <td> <p>Classic book-style slot, mystery symbol triggers bonus rounds</p> </td> </tr> <tr> <td> <p>Book of Blarney GigaBlox</p> </td> <td> <p>Reflexgaming</p> </td> <td> <p>96.2%</p> </td> <td> <p>Irish luck theme, GigaBlox mechanics, stacked symbols</p> </td> </tr> <tr> <td> <p>Book of Cats Megaways</p> </td> <td> <p>BGaming</p> </td> <td> <p>96.3%</p> </td> <td> <p>Megaways format, multiple ways to win, expanding wild symbol</p> </td> </tr> <tr> <td> <p>Book of Nile: Revenge</p> </td> <td> <p>NetGame</p> </td> <td> <p>95.9%</p> </td> <td> <p>Adventure theme, free spins with retrigger, high volatility</p> </td> </tr> <tr> <td> <p>Book of Gold</p> </td> <td> <p>TaDa Gaming</p> </td> <td> <p>96.0%</p> </td> <td> <p>Timeless slot design, scatter symbol triggers 10 free spins</p> </td> </tr> <tr> <td> <p>Book of Faith</p> </td> <td> <p>VoltEnt</p> </td> <td> <p>96.4%</p> </td> <td> <p>Collect-to-Infinity feature, progressive multipliers</p> </td> </tr> <tr> <td> <p>Book of Olympus</p> </td> <td> <p>Apparat Gaming</p> </td> <td> <p>96.1%</p> </td> <td> <p>Mythological theme, Zeus feature, trigger lightning spins</p> </td> </tr> <tr> <td> <p>Book of Poseidon</p> </td> <td> <p>Booming Games</p> </td> <td> <p>96.5%</p> </td> <td> <p>Underwater adventure, stacked wilds, retriggerable free spins</p> </td> </tr> <tr> <td> <p>Book of Kemet</p> </td> <td> <p>BGaming</p> </td> <td> <p>96.2%</p> </td> <td> <p>Archaeology theme, bonus symbol unlocks jackpot action</p> </td> </tr> </tbody> </table> </section> <section> <p>Each of these titles has been created with players in mind, offering not only striking graphics but also fair RTP values that protect your bankroll while keeping every session filled with excitement. If you want to try your skills and strategies - you can visit our <a href="/games/table">real money casino table games</a> section.</p> </section> <section> <h2>Bonuses for Top Book Casino Games</h2> <p>At Zoome, we know that our players appreciate more than just entertaining casino games &mdash; they want added value that can truly trigger exciting rounds and increase their chances to win. That&rsquo;s why every one of our top book slots and other favourites comes with unique bonuses.</p> <p>Here&rsquo;s how Zoome rewards you when you choose popular games:</p> <ul> <li>Book of Cats Megaways (BGaming) &ndash; Receive up to 100 free spins when you land special scatter symbols. The Megaways mechanic increases the number of ways to win during every spin.</li> <li>Book of Faith (VoltEnt) &ndash; Take part in Collect-to-Infinity challenges where multipliers continue starting from your first round. The more you collect, the higher your reward.</li> <li>Book of Olympus (Apparat Gaming) &ndash; Unlock lightning features, where Zeus himself will randomly trigger expanding reels, giving players a chance to beat the odds.</li> <li>Book of Poseidon (Booming Games) &ndash; A watery adventure that provides up to 50 retriggerable free spins, perfect for long <a href="/games/arcade">arcade gaming</a> sessions.</li> </ul> <p>These bonuses are created to maximise your experience. Every round adds more excitement, making sure that your journey through the reels is as rewarding as possible.</p> </section> <section> <h3>Welcome Packages at Zoome</h3> <p>When new players join Zoome Casino, they receive more than just access to the best casino games. Our welcome packages are designed to kickstart your journey with added value.</p> <p>What You Get in the Welcome Offer:</p> <ul> <li>First Deposit Bonus &ndash; 100% match bonus up to AUD 1,000, instantly doubling your bankroll.</li> <li>Free Spins &ndash; 250 spins spread across the most popular book slots, including Book of Nibiru, Book of Gold, and Book of Nile: Revenge.</li> <li>Extra Bets &ndash; Exclusive vouchers that allow new players to place additional bets on <a href="/games/live">live dealer casino</a> tables such as roulette and blackjack.</li> </ul> <p>Note: All welcome rewards are subject to standard terms, and players must apply them within the first 30 days after registration.</p> <p>This package is designed with your bankroll in mind, ensuring you get the most out of your starting point at Zoome. With it, you&rsquo;re ready to explore every corner of our casino, from book-themed adventures to fast-paced card tables.</p> </section> <section> <h3>Free Spins on Popular Slots</h3> <p>One of the most exciting features at Zoome Casino is the chance to unlock free spins on some of our most beloved pokies. These aren&rsquo;t just promotional gimmicks &mdash; they are opportunities for players to extend their sessions, discover new symbols, and maximise their chances to win.</p> <p>Here are just a few of the games where free spins are available:</p> </section> <section> <table> <tbody> <tr> <td> <p>Slot Title</p> </td> <td> <p>Free Spins Offer</p> </td> <td> <p>Special Feature</p> </td> </tr> <tr> <td> <p>Book of Wild (1spin4win)</p> </td> <td> <p>100 free spins for first-time depositors</p> </td> <td> <p>Mystery expanding symbol</p> </td> </tr> <tr> <td> <p>Book of Blarney GigaBlox</p> </td> <td> <p>150 free spins every Friday</p> </td> <td> <p>GigaBlox mechanic creates massive symbols</p> </td> </tr> <tr> <td> <p>Book of Nile: Revenge</p> </td> <td> <p>50 free spins for second deposit</p> </td> <td> <p>Retriggerable free spins</p> </td> </tr> <tr> <td> <p>Book of Gold (TaDa Gaming)</p> </td> <td> <p>20-50 free spins in seasonal promotions</p> </td> <td> <p>Scatter symbol unlocks the bonus round</p> </td> </tr> <tr> <td> <p>Book of Kemet (BGaming)</p> </td> <td> <p>100 free spins for third deposit</p> </td> <td> <p>Jackpot symbol and wild multipliers</p> </td> </tr> </tbody> </table> </section> <section> <p>With these offers, every spin becomes an adventure. Imagine entering ancient tombs, spinning the wheel of fortune, and walking away with life-changing payouts. It&rsquo;s not just about making bets; it&rsquo;s about creating memorable sessions filled with excitement.</p> </section> <section> <h3>Live Casino Cashback</h3> <p>Zoome Casino offers a Live Casino cashback program, so our customers always feel protected. Whenever you play at our live tables &mdash; whether it&rsquo;s <a href="/games/roulette">roulette game</a>, blackjack, or poker &mdash; you&rsquo;ll receive a percentage of your losses back as cashback.</p> <p>How Cashback Works:</p> <ul> <li>Eligibility &ndash; Available on all live casino games, including craps and card tables.</li> <li>Percentage &ndash; Up to 20% cashback on net losses, credited every Monday.</li> <li>Applies to &ndash; Classic and modern live dealer games from top providers.</li> </ul> <p>This feature is created to protect your bankroll and give you peace of mind, even if the wheel doesn&rsquo;t land in your favour. Every day of play at Zoome comes with added safety, making your casino gambling journey fairer and more enjoyable.</p> </section> <section> <h2>Casino Gambling Tournaments &amp; Seasonal Promotions</h2> <p>At Zoome Casino, we believe gaming is more than just individual bets &mdash; it&rsquo;s about community, competition, and celebration. That&rsquo;s why we host regular tournaments and exclusive seasonal promotions for our players.</p> <p>Types of Tournaments:</p> <ul> <li>Slots Tournaments &ndash; Compete in book casino games like Book of Olympus or Book of Faith for leaderboard prizes.</li> <li>Table Game Challenges &ndash; Make strategic bets in <a href="/games/blackjack">online blackjack real money</a> or poker to climb the ranks.</li> <li>Roulette Wheel Races &ndash; Spin the wheel, collect points, and chase daily rewards.</li> </ul> <p>Seasonal Promotions Include:</p> <ul> <li>Holiday Free Spin Extravaganzas &ndash; Christmas and New Year promos with hundreds of free spins on top-rated pokies.</li> <li>Summer Jackpots &ndash; Exclusive prize pools across multiple games, starting every June.</li> <li>Halloween Book Specials &ndash; Dark-themed book games like Book of Darkness and Book of Doom offering mystery symbol features.</li> </ul> <p>Every promotion is carefully created to ensure players not only enjoy the thrill of competition but also have more chances to win. Whether you&rsquo;re chasing leaderboard glory or claiming festive offers, Zoome Casino always keeps the action alive.</p> </section> <section> <h2>Why Players Choose These Gaming Options</h2> <p>When it comes to choosing a place to play, Zoome Casino stands out in the world of online gambling. Here&rsquo;s why thousands of customers trust our platform and keep coming back:</p> </section> <section> <h3>High RTP</h3> <p>Our book pokies and table games offer RTP percentages that consistently rank above industry average. With rates ranging from 95% to 97%, players can feel confident that their bets are fairly rewarded.</p> </section> <section> <h3>Exciting Gameplay</h3> <p>Each game is filled with immersive features: free rounds, expanding symbols, retriggers, unique strategy testing in <a href="/games/baccarat">free online baccarat</a>, and jackpot bonuses. Whether you&rsquo;re starting with a single spin on Book of Nibiru or making a bold card bet in blackjack, the action never stops.</p> </section> <section> <h3>Huge Wins &amp; Jackpots</h3> <p>Zoome Casino gives you a chance to beat the odds and unlock life-changing payouts. From progressive jackpots on themed pokies to high-stakes <a href="/games/poker_games">Texas poker online</a> tournaments, our platform ensures that every player can chase a big win.</p> </section> <section> <h3>Mobile Accessibility</h3> <p>Modern gaming means flexibility. That&rsquo;s why all of our casino games &mdash; from <a href="/games/keno_games">online keno Australia</a> to adventure-filled book slots &mdash; are fully optimised for smartphones. Whether you land on iOS or Android, your experience remains smooth, responsive, and visually striking.</p> </section> <section> <h3>Trust &amp; Protection</h3> <p>Our system is created to protect players, ensuring fair play and reliable payouts. Add to this 24/7 customer support, and you have a casino that puts customers first.</p> </section> <section> <h2>Mobile Gaming Options at Zoome</h2> <p>The modern world of online entertainment demands flexibility, and Zoome Casino delivers. All of our casino games, from classic roulette and blackjack tables to innovative <a href="/games/coins">coin games online</a>, are fully optimised for mobile play.</p> <ul> <li>Compatibility &ndash; Works seamlessly on iOS and Android devices.</li> <li>Smartphone Design &ndash; An interface specifically created to adapt to smaller screens.</li> <li>Convenience &ndash; Take your casino gambling wherever you land, whether you&rsquo;re commuting or relaxing at home.</li> </ul> <p>With just a few taps, you can access our full range of titles, claim offers, and spin the reels. Our platform ensures you never miss a chance to win, even while on the move.</p> </section> <section> <h2>Conclusion</h2> <p>Zoome Casino isn&rsquo;t just another site; it&rsquo;s a carefully created platform designed with players in mind. From legendary <a href="/games/top_au">top casino slot games</a> like Book of Gold and Book of Olympus, to exciting tables where you can test your poker or blackjack skills, every spin and every card carries the potential to win big.</p> <p>Here&rsquo;s the final word: if you&rsquo;re ready to discover a platform filled with excitement, fairness, and incredible gaming options, Zoome Casino is the place to be.</p> <p>Start making bets, spin the wheel, and find your fortune in the Zoome world of online entertainment. The adventure is only starting &mdash; and the next big jackpot could be yours.</p> </section> <h2>FAQ Section</h2> <h3>What makes Zoome Casino different from other platforms?</h3> <p>Our focus is on variety and fairness. With high-RTP book casino games, competitive promotions, and 24/7 support, we provide the best experience possible.</p> <h3>Can I play on mobile devices?</h3> <p>Yes. Zoome is optimised for iOS and Android, ensuring smooth sessions anywhere.</p> <h3>How do I claim my welcome package?</h3> <p>Simply make your first deposit and the bonus will automatically apply. Full details are available on the promotions page.</p> <h3>Which payment methods are accepted?</h3> <p>We support a wide range of options &mdash; from credit card payments to e-wallets.</p> <h3>Do the games have fair outcomes?</h3> <p>Absolutely. Every title is RNG-tested, which helps protect our customers and guarantees fair pays.</p> <h3>Can I set a responsible gambling limit?</h3> <p>Yes. Zoome allows players to manage their sessions, set a date for limits, and keep close control over their play.</p> <h3>Do I get rewards for loyalty?</h3> <p>Yes. Regular players can enjoy exclusive cashback, cart-style reward collections, and seasonal offers.</p> <h3>Is there any reading material or guides for beginners?</h3> <p>Of course. Our blog and help centre contain useful reading guides on how to play poker, roulette, craps, and slots.</p> СТРОГИЙ ПРИМЕР Пример входа (сырой текст)

LuckyHills Casino: welcome bonus 100% + 100 FS (min 20 EUR) и 200% на второй депозит с 40 EUR; платежи Visa/Mastercard/Bitcoin; поддержка 24/7; выплаты до 60 минут. AU-фокус.

Комментарии к ожидаемому выходу (для тебя, не выводить в ответ модели):

Во всём шаблоне «Zoome» заменить на «LuckyHills».

Цифры бонусов подставить в соответствующие абзацы/списки.

Если данные отсутствуют — использовать нейтральные заглушки.

В реальном ответе вернуть только HTML из шаблона, заполненный текстом, без этого раздела.

ВХОД

SOURCE_TEXT: Тут должен быть текст который вставил юзер
'''"""
# ---------- /ВСТАВЬ СВОИ ПРОМПТЫ НИЖЕ ----------

# Карта выбора
PROMPTS: Dict[str, str] = {
    "1) Admin #1 (HTML_PROMPT)": HTML_PROMPT,
    "2) Admin #2 (WS/LH)": HTML_PROMPT_WS_LH,
    "3) Admin #3 (Zoome)": HTML_PROMPT_ZOOME,
}


def setup_page() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="🧩", layout="wide")
    st.markdown(
        """
        <style>
          [data-testid="stSidebar"], [data-testid="collapsedControl"], header { display:none!important; }
          .block-container { padding-top: 2rem; }
          .stButton>button { height:48px; font-weight:600; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def guard_secrets() -> None:
    if not OPENAI_KEY:
        st.error("Не найден OPENAI_API_KEY в secrets.")
        st.stop()


def looks_like_html(s: str) -> bool:
    t = (s or "").strip().lower()
    return t.startswith("<!doctype") or (t.startswith("<") and "</" in t)


def strip_code_fences(text: str) -> str:
    t = (text or "").strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1]
    if t.endswith("```"):
        t = t[:-3]
    return t.strip()


def build_final_prompt(base_prompt: str, user_text: str) -> str:
    """
    ВАЖНО: Отправляем ВМЕСТЕ и промпт (с примерами/шаблонами), и реальный текст юзера.
    1) Если внутри промпта есть фраза-плейсхолдер — заменяем её.
    2) Если нет — добавляем в конец явный блок SOURCE_TEXT (OVERRIDE).
    Это убивает кейс, когда модель "залипает" на пример из промпта.
    """
    if not base_prompt:
        return user_text

    ut = (user_text or "").strip()

    if PLACEHOLDER in base_prompt:
        merged = base_prompt.replace(PLACEHOLDER, ut)
    else:
        merged = (
            base_prompt
            + "\n\n===== SOURCE_TEXT (OVERRIDE ANY EXAMPLES ABOVE) =====\n"
            + ut
            + "\n===== /SOURCE_TEXT ====="
        )

    return merged


def call_openai_with_prompt(final_prompt: str) -> str:
    client = OpenAI(api_key=OPENAI_KEY)

    # Попытка через Responses API
    try:
        r = client.responses.create(model=MODEL, input=final_prompt)
        if getattr(r, "output_text", None):
            return strip_code_fences(r.output_text)

        # универсальная сборка на случай иной формы
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
        # Фолбэк на chat.completions
        c = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": final_prompt}],
        )
        return strip_code_fences(c.choices[0].message.content)


def main() -> None:
    setup_page()
    guard_secrets()

    st.title(APP_TITLE)

    # Выбор админки/промпта
    which = st.selectbox(
        "Выбери админку (промпт):",
        options=list(PROMPTS.keys()),
        index=0,
    )

    raw_text = st.text_area(
        "Исходный текст пользователя (подставится ВНУТРЬ промпта)",
        height=300,
        placeholder="Вставьте контент…",
        key="raw_text",
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        do_generate = st.button("🚀 Сгенерировать", type="primary", use_container_width=True)
    with col2:
        if st.button("🧹 Очистить", use_container_width=True):
            st.session_state["raw_text"] = ""
            st.experimental_rerun()

    st.caption(f"Используется захардкоженный промпт: **{which}**")

    if do_generate:
        if not raw_text or not raw_text.strip():
            st.error("Введите текст пользователя.")
            st.stop()

        base = PROMPTS.get(which, "")
        final_prompt = build_final_prompt(base, raw_text)

        with st.spinner("Генерация…"):
            try:
                out = call_openai_with_prompt(final_prompt)
            except Exception as e:
                st.exception(e)
                st.stop()

        st.subheader("Результат (без изменений)")
        if looks_like_html(out):
            components.html(out, height=PREVIEW_HEIGHT, scrolling=True)
            st.download_button(
                "💾 Скачать как HTML",
                out,
                file_name=f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                mime="text/html",
                use_container_width=True,
            )
        else:
            st.write(out)

        with st.expander("Показать как текст"):
            st.code(out, language="html")

        st.caption(
            "Мы отправили ВМЕСТЕ: твой промпт + пример/шаблон + текст пользователя. "
            "Если результат не соответствует — корректируй сам промпт в коде."
        )


if __name__ == "__main__":
    main()
