#!/usr/bin/env python3
"""Generate individual city/neighborhood pages for Ben Lee Properties."""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
CITIES_DIR = os.path.join(BASE, 'cities')
os.makedirs(CITIES_DIR, exist_ok=True)

# ── Neighborhood data ────────────────────────────────────────────────────────

NEIGHBORHOODS = [
    {
        "slug": "cheviot-hills",
        "name": "Cheviot Hills",
        "tagline": "LA's Most Established Westside Community",
        "zip": "90064",
        "geo_lat": 34.0333,
        "geo_lon": -118.4167,
        "hero_img": "../images/pexels-max-vakhtbovych-6969828_1pexels-max-vakhtbovych-6969828.avif",
        "hero_img_alt": "Cheviot Hills home",
        "meta_desc": "Cheviot Hills real estate guide from Ben Lee, the top broker in the neighborhood. Median home price $3M, developed in the 1920s, between Fox and Sony studios. Expert buyer and seller representation.",
        "og_desc": "Ben Lee is the top-producing broker in Cheviot Hills. Get hyper-local market data, school info, and expert representation in this premier West LA neighborhood.",
        "median_price": "$3,000,000",
        "price_trend": "up 0.1% year over year",
        "avg_dom": "36 days",
        "price_note": "Homes range from approximately $1.4M for ranch-style bungalows to $8.5M+ for newer two-story properties.",
        "about": (
            "Cheviot Hills is one of the most sought-after residential communities on the Westside of Los Angeles. "
            "Developed in the 1920s, the neighborhood sits between the Fox Studios and Sony Pictures lots, making it a natural home "
            "for entertainment industry professionals and their families. Its tree-lined streets, wide lots, and proximity to Century City "
            "and Culver City give it a rare combination of calm and convenience."
            "<br><br>"
            "The neighborhood consistently ranks among the wealthiest 3.5% in the United States. "
            "It offers public and private golf courses, pools, and tennis courts within its borders. "
            "Homes here range from original 1920s bungalows and ranch-style houses to newer two-story builds, "
            "giving buyers a wide range of price points within the same desirable zip code."
        ),
        "schools": [
            ("Overland Avenue Elementary", "A California Distinguished School, one of the most respected public elementary schools in West Los Angeles."),
            ("Alexander Hamilton High School", "Home to a renowned performing arts magnet that draws students from across the city."),
            ("Palms Middle School", "Nearby public middle school serving the 90064 zip code."),
        ],
        "features": [
            "Situated between Fox Studios and Sony Pictures",
            "Top 3.5% wealthiest neighborhoods in the United States",
            "Golf courses, pools, and tennis courts within the community",
            "Close proximity to Century City, Culver City, and Beverly Hills",
            "Quiet, residential streets with minimal through-traffic",
            "Strong appreciation history since the 1920s",
        ],
        "ben_note": (
            "Ben Lee has closed more transactions in Cheviot Hills than any other broker operating in the area. "
            "His deep knowledge of the neighborhood's micro-pockets, pricing dynamics, and off-market opportunities "
            "is what consistently delivers above-asking results for sellers and below-list deals for buyers."
        ),
        "faqs": [
            ("What is the median home price in Cheviot Hills?",
             "As of early 2026, the median sale price in Cheviot Hills is approximately $3,000,000. Prices range from around $1.4M for original ranch-style homes to $8.5M and above for newer two-story builds. The market has remained stable year over year."),
            ("What schools serve Cheviot Hills?",
             "Cheviot Hills is served by Overland Avenue Elementary School, a California Distinguished School. Hamilton High School nearby has a nationally recognized performing arts magnet program. The neighborhood falls within the Los Angeles Unified School District."),
            ("Why do people choose to live in Cheviot Hills?",
             "Cheviot Hills offers a rare combination of central Westside location, quiet residential streets, a strong sense of community, and access to excellent schools. It sits between Fox Studios and Sony Pictures, making it popular with entertainment industry professionals. Golf courses, tennis courts, and pools are available within the neighborhood itself."),
            ("How long do homes typically stay on the market in Cheviot Hills?",
             "Homes in Cheviot Hills sell in approximately 36 days on average, faster than the prior year average of 43 days. Well-priced homes in desirable pockets can receive multiple offers within the first week of listing."),
            ("Who is the top real estate agent in Cheviot Hills?",
             "Ben Lee of Ben Lee Properties is the top-producing broker in Cheviot Hills. With over $1 billion in closed transactions across the Westside and a monthly newsletter reaching 9,000+ neighborhood households, Ben provides both market reach and hyper-local expertise that national firms cannot match."),
        ],
    },
    {
        "slug": "beverlywood",
        "name": "Beverlywood",
        "tagline": "A Master-Planned Community Bordering Beverly Hills",
        "zip": "90034",
        "geo_lat": 34.0472,
        "geo_lon": -118.3986,
        "hero_img": "../images/pexels-max-vakhtbovych-6058444_1pexels-max-vakhtbovych-6058444.avif",
        "hero_img_alt": "Beverlywood home",
        "meta_desc": "Beverlywood real estate guide from Ben Lee Properties. Median sale price $2.6M, tree-lined streets, Beverlywood Homes Association, top-rated elementary schools. Expert buyer and seller representation.",
        "og_desc": "Ben Lee Properties specializes in Beverlywood real estate. Get current market data, school info, and expert representation in this hidden gem adjacent to Beverly Hills.",
        "median_price": "$2,600,000",
        "price_trend": "up 10% year over year",
        "avg_dom": "55 days",
        "price_note": "Prices are primarily driven by single-family homes. Condos and townhomes in the 90034 zip trade closer to $975,000.",
        "about": (
            "Beverlywood is a small, master-planned community established in the 1940s on the west side of Los Angeles. "
            "Despite sharing a zip code and neighborhood character with Beverly Hills, it is often called a hidden gem because "
            "its prices have historically trailed its more famous neighbor while offering similar quality of life."
            "<br><br>"
            "About 6,610 people call Beverlywood home. The Beverlywood Homes Association, funded by approximately $1,000 per year "
            "in resident dues, maintains safety programs and works to preserve the neighborhood's distinctive character. "
            "Quiet, tree-lined streets, classic traditional homes, and a central Westside location near Century City and Culver City "
            "make Beverlywood consistently one of the most competitive markets in the 90034 zip code."
        ),
        "schools": [
            ("Canfield Avenue Elementary", "A highly rated public elementary school within the Beverlywood neighborhood boundaries."),
            ("Castle Heights Elementary", "Another top-rated elementary school serving the Beverlywood community."),
            ("Palms Middle School", "Nearby public middle school serving the western 90034 corridor."),
        ],
        "features": [
            "Master-planned community established in the 1940s",
            "Beverlywood Homes Association provides community oversight and safety programs",
            "Adjacent to Beverly Hills and Century City",
            "Tree-lined residential streets with low through-traffic",
            "Mix of classic traditional homes and newer luxury construction",
            "Stabilizing toward moderate growth after the 2022-2025 market correction",
        ],
        "ben_note": (
            "Ben Lee has covered Beverlywood as part of his core territory since the beginning of his career. "
            "His monthly newsletter is mailed directly to Beverlywood households, giving his seller listings "
            "immediate reach within the community. His understanding of which streets and pockets command premiums "
            "is a direct asset to buyers and sellers alike."
        ),
        "faqs": [
            ("What is the median home price in Beverlywood?",
             "The median sale price in Beverlywood over the last 12 months is approximately $2,600,000, up 10% from the prior year. The market is moderately competitive, with homes typically selling within 55 days. Condos and townhomes in the 90034 zip trade closer to $975,000."),
            ("What makes Beverlywood different from Beverly Hills?",
             "Beverlywood is an unincorporated community adjacent to Beverly Hills, within Los Angeles city limits. It has its own homeowners association (Beverlywood Homes Association), top-rated elementary schools, and a quieter residential character. Home prices are generally lower than in Beverly Hills proper, making it an attractive alternative for buyers priced out of 90210."),
            ("What schools serve Beverlywood?",
             "Beverlywood is served by Canfield Avenue Elementary and Castle Heights Elementary, both of which are highly rated within the Los Angeles Unified School District. Palms Middle School serves the broader area."),
            ("Is Beverlywood a good investment?",
             "Beverlywood has shown strong long-term appreciation and is moving from a post-2022 correction into a phase of stabilization and moderate growth in 2026-2028. The combination of constrained supply, central Westside location, and top-rated schools makes it a reliable long-term hold."),
            ("Who is the best real estate agent in Beverlywood?",
             "Ben Lee of Ben Lee Properties has covered Beverlywood as a primary service area for over 15 years. His monthly newsletter reaches Beverlywood households directly, and his track record of above-asking sales in the neighborhood is backed by over $1 billion in closed Westside transactions."),
        ],
    },
    {
        "slug": "beverly-hills",
        "name": "Beverly Hills",
        "tagline": "The Platinum Triangle and the World's Most Famous Address",
        "zip": "90210",
        "geo_lat": 34.0736,
        "geo_lon": -118.4004,
        "hero_img": "../images/pexels-vincent-gerbouin-445991-2263683.jpg",
        "hero_img_alt": "Beverly Hills luxury home",
        "meta_desc": "Beverly Hills real estate guide from Ben Lee Properties, based at 9454 Wilshire Blvd. Median SFR price $4.85M. Expert buyer and seller representation in 90210 from a licensed broker and attorney.",
        "og_desc": "Ben Lee Properties is based in Beverly Hills. Get expert real estate guidance in 90210, the Flats, and the Platinum Triangle from a licensed broker and attorney with $1B+ in closed deals.",
        "median_price": "$4,850,000",
        "price_trend": "steady, with modest 2-4% annual growth projected",
        "avg_dom": "117 days",
        "price_note": "Entry-level tear-downs in the Flats start at $7M-$9M. Fully renovated properties command considerably more. High-end estates above $8M see fewer but highly strategic transactions.",
        "about": (
            "Beverly Hills is one of the most recognized addresses in the world. The city covers approximately 5.7 square miles "
            "and is home to around 33,700 residents. Its famous Rodeo Drive shopping district, Platinum Triangle designation "
            "alongside Bel Air and Holmby Hills, and world-class dining and hospitality make it a global real estate benchmark."
            "<br><br>"
            "The residential heart of Beverly Hills is largely in the Flats, a grid of wide streets bounded by Santa Monica Boulevard, "
            "Sunset Boulevard, Doheny Drive, and Whittier Drive. North of Sunset, the estates climb into the hills with increasing "
            "privacy and scale. In 2026, the market is shifting toward more balanced conditions as inventory grows modestly "
            "and mortgage rates ease, creating better buyer leverage than seen in recent years."
        ),
        "schools": [
            ("Beverly Hills Unified School District", "A standalone district covering four K-8 schools: El Rodeo, Hawthorne, Beverly Vista, and Horace Mann."),
            ("Beverly Hills High School", "One of California's most recognized public high schools, with alumni spanning film, business, and government."),
            ("Moreno High School", "A continuation high school within the Beverly Hills Unified District."),
        ],
        "features": [
            "Part of the Platinum Triangle alongside Bel Air and Holmby Hills",
            "Home to Ben Lee's primary brokerage office at 9454 Wilshire Blvd",
            "Rodeo Drive and world-class retail and hospitality",
            "Standalone Beverly Hills Unified School District",
            "Population of approximately 33,700 with a median age of 46.9",
            "2026 market shifting toward balanced conditions with improved buyer leverage",
        ],
        "ben_note": (
            "Ben Lee operates his primary brokerage out of Beverly Hills' number one office at 9454 Wilshire Blvd. "
            "As a licensed attorney and broker, he brings a level of legal expertise to Beverly Hills negotiations "
            "that most agents simply cannot match. Whether you are buying a property in the Flats or listing an estate "
            "north of Sunset, Ben's track record in this market speaks for itself."
        ),
        "faqs": [
            ("What is the median home price in Beverly Hills?",
             "The median sale price for a single-family residence in Beverly Hills is approximately $4,850,000 as of early 2026. Entry-level properties in the Flats, often needing renovation, start at $7M-$9M for tear-downs. The broader median including condos and all property types sits closer to $3.4M."),
            ("How long do homes take to sell in Beverly Hills?",
             "Homes in Beverly Hills currently average about 117 days on market, up from 54 days the prior year. The luxury segment above $8M is highly strategic and negotiation-driven. Below $3.5M, competition is sharper with multiple offers common."),
            ("What schools serve Beverly Hills residents?",
             "Beverly Hills has its own standalone school district, Beverly Hills Unified, serving approximately 3,074 students. The district includes El Rodeo, Hawthorne, Beverly Vista, and Horace Mann (K-8 schools), Moreno High School, and the well-known Beverly Hills High School."),
            ("What neighborhoods make up Beverly Hills?",
             "The main residential areas include the Beverly Hills Flats (south of Sunset), the Trousdale Estates, and the hillside areas north of Sunset leading toward Bel Air. Together with Bel Air and Holmby Hills, Beverly Hills forms the Platinum Triangle."),
            ("Who is the best real estate broker in Beverly Hills?",
             "Ben Lee is the top-producing broker at Beverly Hills' number one office (9454 Wilshire Blvd). He is a licensed California broker and attorney with over $1 billion in closed transactions. His legal background is a significant advantage in Beverly Hills negotiations, where deal complexity is above average."),
        ],
    },
    {
        "slug": "west-los-angeles",
        "name": "West Los Angeles",
        "tagline": "Central Westside Access at a More Approachable Price Point",
        "zip": "90064",
        "geo_lat": 34.0367,
        "geo_lon": -118.4472,
        "hero_img": "../images/pexels-curtis-adams-5353877_1pexels-curtis-adams-5353877.avif",
        "hero_img_alt": "West Los Angeles home",
        "meta_desc": "West Los Angeles real estate guide from Ben Lee Properties. Median home price $1.4M, 28 days on market, strong walkability in pockets. Ben Lee's second office is at 11500 W Olympic Blvd.",
        "og_desc": "Ben Lee Properties covers West Los Angeles from their office at 11500 W Olympic Blvd. Get current market data and expert representation for West LA buyers and sellers.",
        "median_price": "$1,405,000",
        "price_trend": "up 7% year over year",
        "avg_dom": "28 days",
        "price_note": "West LA offers the most accessible price point among Ben Lee's core Westside markets, with strong demand from UCLA affiliates, tech workers, and young families.",
        "about": (
            "West Los Angeles occupies a strategically central position on the Westside, stretching roughly from the 405 Freeway "
            "to the UCLA campus. It offers convenient access to Santa Monica, Culver City, Century City, and the 10 and 405 freeways, "
            "making it one of the most practical neighborhoods for professionals who need to move across the region."
            "<br><br>"
            "Ben Lee's second office is located at 11500 W Olympic Blvd, placing his team directly in the community. "
            "West LA is one of the fastest-moving markets in the portfolio, with homes selling in an average of just 28 days. "
            "Pockets like Palms have a Walk Score of 90, and the neighborhood's mix of single-family homes, condos, and "
            "smaller apartment buildings appeals to a wide range of buyers and investors."
        ),
        "schools": [
            ("Westwood Elementary School", "A well-regarded public elementary school serving the northern portion of West LA near Westwood Village."),
            ("Palms Elementary School", "Public elementary school in the walkable Palms pocket of West Los Angeles."),
            ("Hamilton High School", "A large LAUSD high school with a nationally recognized performing arts magnet program."),
        ],
        "features": [
            "Ben Lee's second office located at 11500 W Olympic Blvd",
            "Fastest-moving market in the Ben Lee portfolio, averaging 28 days on market",
            "Palms pocket has a Walk Score of 90",
            "Strong demand from UCLA affiliates, healthcare workers, and tech professionals",
            "Access to the 405 and 10 freeways, Santa Monica, and Century City",
            "Diverse mix of single-family homes, condos, and income properties",
        ],
        "ben_note": (
            "Ben Lee operates his West Los Angeles office at 11500 W Olympic Blvd. "
            "His monthly newsletter reaches thousands of West LA households, giving his sellers "
            "built-in neighborhood exposure before a property ever hits the MLS. "
            "For buyers, his on-the-ground knowledge of which streets offer the best long-term appreciation is invaluable."
        ),
        "faqs": [
            ("What is the median home price in West Los Angeles?",
             "The median sale price in West Los Angeles is approximately $1,405,000 as of early 2026, up 7% year over year. The average sale price, skewed by larger homes, sits closer to $1,650,000. West LA is the most accessible price point among Ben Lee's core Westside neighborhoods."),
            ("How fast do homes sell in West Los Angeles?",
             "Homes in West Los Angeles sell in an average of 28 days, making it one of the fastest-moving markets on the Westside. Well-priced, updated homes in desirable pockets can attract offers within days of listing."),
            ("What makes West Los Angeles a good place to buy?",
             "West LA offers central Westside access at prices below Beverly Hills and Brentwood. The Palms pocket has a Walk Score of 90. It is close to UCLA, Santa Monica, Culver City, and Century City. Strong rental demand from university affiliates and tech workers also makes it an attractive investment market."),
            ("Where is Ben Lee's West Los Angeles office?",
             "Ben Lee's West Los Angeles office is located at 11500 W Olympic Blvd, Los Angeles, CA 90064. You can reach Ben directly at (310) 704-6580 or ben@benleeproperties.com."),
            ("What types of properties are available in West LA?",
             "West Los Angeles offers a wide range of property types including single-family homes, condos, townhomes, duplexes, and small apartment buildings. This diversity makes it attractive to both owner-occupants and investors looking for rental income."),
        ],
    },
    {
        "slug": "bel-air",
        "name": "Bel Air",
        "tagline": "Gated Estates and Privacy in the Santa Monica Mountains",
        "zip": "90077",
        "geo_lat": 34.0903,
        "geo_lon": -118.4526,
        "hero_img": "../images/pexels-alexandr-podvalny-7599735_1pexels-alexandr-podvalny-7599735.avif",
        "hero_img_alt": "Bel Air estate",
        "meta_desc": "Bel Air real estate guide from Ben Lee Properties. Median list price $8.1M, 7+ months of inventory creating buyer leverage. Part of the Platinum Triangle. Expert luxury representation.",
        "og_desc": "Bel Air is entering a buyer-favorable market in 2026 with 7+ months of inventory. Ben Lee provides expert representation in this ultra-luxury Westside neighborhood.",
        "median_price": "$8,147,000",
        "price_trend": "buyer-favorable, with 7+ months of inventory",
        "avg_dom": "varies by property tier",
        "price_note": "Bel Air has entered a buyer's market as of 2025-2026, with inventory above 7 months. Buyers have more leverage than at any point in the last several years.",
        "about": (
            "Bel Air is one of three neighborhoods that form the Platinum Triangle of Los Angeles, alongside Beverly Hills and Holmby Hills. "
            "Nestled in the foothills of the Santa Monica Mountains, it is characterized by gated communities, sweeping canyon and city views, "
            "and estates that range from architectural masterpieces to sprawling traditional compounds."
            "<br><br>"
            "In 2025-2026, Bel Air has transitioned into a buyer's market with over 7 months of available inventory. "
            "A balanced market typically sits between 4 and 6 months, meaning buyers currently have meaningful leverage "
            "not seen in recent cycles. The Median List Price for a single-family residence in Bel Air sits at approximately $8,147,000, "
            "while properties at the ultra-luxury tier can reach nine figures."
        ),
        "schools": [
            ("Bel Air Elementary School", "A well-regarded public elementary school within the neighborhood boundaries."),
            ("Paul Revere Middle School", "One of the top-ranked public middle schools in LAUSD, nearby in Brentwood."),
            ("University High School", "A large LAUSD high school serving portions of Bel Air and the surrounding Westside."),
        ],
        "features": [
            "Part of the Platinum Triangle with Beverly Hills and Holmby Hills",
            "Gated communities and estates with canyon and city views",
            "Current buyer's market with 7+ months of inventory",
            "Prices range from $4M starter estates to nine-figure trophies",
            "Access to premium private schools in Beverly Hills and Brentwood",
            "Proximity to the 405 and Sunset Boulevard",
        ],
        "ben_note": (
            "In ultra-luxury markets like Bel Air, the difference between a good agent and the right agent is measured in millions. "
            "Ben Lee's background as a licensed attorney gives him a unique edge in complex negotiations, "
            "trust structures, and off-market transactions. He brings the same disciplined, data-driven approach "
            "to an $8M Bel Air estate that he applies to every transaction in his portfolio."
        ),
        "faqs": [
            ("What is the median home price in Bel Air?",
             "The median list price for a single-family home in Bel Air is approximately $8,147,000 as of 2026. Actual sale prices vary significantly by property, view, condition, and lot size. The market is currently in buyer-favorable territory with over 7 months of inventory."),
            ("Is now a good time to buy in Bel Air?",
             "Yes. Bel Air has crossed the 7-month inventory threshold, indicating a buyer's market. A balanced market sits between 4 and 6 months of supply. Buyers in 2026 have more negotiating leverage than at any point in recent years. For qualified buyers, this is a rare window."),
            ("What neighborhoods border Bel Air?",
             "Bel Air borders Beverly Hills to the south, Brentwood to the west, and Holmby Hills to the east. Together with Beverly Hills and Holmby Hills, it forms the Platinum Triangle of Los Angeles."),
            ("What makes Bel Air different from Beverly Hills?",
             "Bel Air is more secluded and canyon-oriented than Beverly Hills. Properties are often gated and offer more land, privacy, and views. There is no commercial district in Bel Air itself. It tends to attract buyers who prioritize privacy and scale over walkability."),
            ("Who handles luxury real estate in Bel Air?",
             "Ben Lee of Ben Lee Properties provides expert representation for Bel Air buyers and sellers. As a licensed broker and attorney, Ben navigates the legal and financial complexity of high-value transactions with precision. His Beverly Hills office at 9454 Wilshire Blvd is minutes from the Bel Air gates."),
        ],
    },
    {
        "slug": "brentwood",
        "name": "Brentwood",
        "tagline": "Coral Trees, the Getty, and One of LA's Most Livable Neighborhoods",
        "zip": "90049",
        "geo_lat": 34.0572,
        "geo_lon": -118.4767,
        "hero_img": "../images/pexels-teona-swift-6913825_1pexels-teona-swift-6913825.avif",
        "hero_img_alt": "Brentwood Los Angeles home",
        "meta_desc": "Brentwood Los Angeles real estate guide from Ben Lee Properties. Median home price $3.25M, top private schools, the Getty Center, and San Vicente's coral trees. Expert buyer and seller representation.",
        "og_desc": "Ben Lee Properties covers Brentwood real estate in Los Angeles. Get current market data, school rankings, and expert representation in 90049 from a licensed broker and attorney.",
        "median_price": "$3,250,000",
        "price_trend": "stable, with strong long-term appreciation driven by constrained supply",
        "avg_dom": "79 days",
        "price_note": "Prices range from $2.5M for standard single-family homes to $20M+ in premier pockets like Brentwood Park and Mandeville Canyon. New construction is limited to teardown-rebuild projects.",
        "about": (
            "Brentwood is a premium residential neighborhood in West Los Angeles covering approximately 7.8 square miles. "
            "It is home to around 34,000 residents and is anchored by iconic landmarks including the Getty Center museum, "
            "the coral tree-lined median of San Vicente Boulevard, and the Brentwood Country Mart. "
            "The neighborhood is nearly fully built out, which keeps supply constrained and supports long-term price stability."
            "<br><br>"
            "Brentwood attracts families who prioritize school quality, professionals who value proximity to the 405 and Santa Monica, "
            "and buyers seeking a neighborhood with genuine community character. Families who purchase in Brentwood for school access "
            "demonstrate longer average tenure than elsewhere in Los Angeles County, a testament to the neighborhood's hold on residents."
        ),
        "schools": [
            ("Kenter Canyon Elementary School", "Rated 9 out of 10 and ranked in the top 10% of LAUSD schools."),
            ("Paul Revere Middle School", "Rated 8 out of 10, also in the top 10% of LAUSD schools."),
            ("Brentwood School", "One of Los Angeles' top five private schools, serving K-12."),
            ("Archer School for Girls", "Another of LA's top five private schools, located on Sunset Boulevard."),
        ],
        "features": [
            "San Vicente Boulevard's iconic coral tree-lined median",
            "The Getty Center, one of LA's premier cultural institutions",
            "Brentwood Country Mart, a beloved retail and dining destination",
            "Nearly fully built out, keeping supply constrained",
            "Top-5 private schools (Brentwood School, Archer School)",
            "Strong long-term appreciation and low turnover",
        ],
        "ben_note": (
            "Brentwood is a neighborhood where relationships and local knowledge matter. "
            "Ben Lee's presence at both his Beverly Hills and West LA offices means he covers Brentwood from two directions. "
            "His monthly newsletter circulates to Brentwood households, keeping his sellers in front of the most engaged "
            "local buyers before a listing goes public."
        ),
        "faqs": [
            ("What is the median home price in Brentwood?",
             "The median home price in Brentwood is approximately $3,250,000 as of late 2025. Prices range from $2.5M for standard single-family homes to $20M+ in Brentwood Park and Mandeville Canyon. Condos range from $800,000 to over $5M for luxury units."),
            ("What schools serve Brentwood?",
             "Brentwood is served by Kenter Canyon Elementary (rated 9/10) and Paul Revere Middle (rated 8/10), both in the top 10% of LAUSD schools. The neighborhood is also home to two of LA's top five private schools: Brentwood School and Archer School for Girls."),
            ("Why do homes in Brentwood hold their value?",
             "Brentwood is nearly fully built out, meaning supply is permanently constrained. New construction is limited to teardown-rebuild projects. Combined with top-rated schools, the Getty Center, and a walkable village (Brentwood Country Mart, San Vicente corridor), demand consistently outpaces available inventory."),
            ("What is the Brentwood Country Mart?",
             "Brentwood Country Mart is a beloved open-air retail and dining complex on 26th Street and San Vicente Boulevard. It has served as a neighborhood gathering point since 1948 and includes restaurants, boutiques, and farmers market events."),
            ("How does Ben Lee cover the Brentwood market?",
             "Ben Lee covers Brentwood from his West LA office at 11500 W Olympic Blvd and his Beverly Hills office at 9454 Wilshire Blvd. His monthly newsletter reaches Brentwood households directly, and his database of active Westside buyers gives sellers an immediate audience before hitting the open market."),
        ],
    },
    {
        "slug": "santa-monica",
        "name": "Santa Monica",
        "tagline": "Coastal Living, Top Schools, and a Beach-City Lifestyle",
        "zip": "90401",
        "geo_lat": 34.0195,
        "geo_lon": -118.4912,
        "hero_img": "../images/pexels-max-vakhtbovych-6969828_1pexels-max-vakhtbovych-6969828.avif",
        "hero_img_alt": "Santa Monica home",
        "meta_desc": "Santa Monica real estate guide from Ben Lee Properties. Median SFR price $3.85M, beach access, top schools, and strict zoning that limits supply. Expert buyer and seller representation.",
        "og_desc": "Ben Lee Properties covers Santa Monica real estate. Get current market data, neighborhood breakdowns, and expert representation in this coastal Westside city.",
        "median_price": "$3,850,000",
        "price_trend": "projected to rise 3.2% through end of 2026",
        "avg_dom": "52 days",
        "price_note": "Single-family homes range from $1.5M in Sunset Park to $4.5M+ north of Montana. Condos start near $1.25M. Strict zoning limits new construction to under 200 units annually.",
        "about": (
            "Santa Monica is an independent coastal city situated just west of Los Angeles, bordered by the Pacific Ocean to the west "
            "and Malibu to the north. It combines beach access, a vibrant downtown, top-rated schools, and strict land use controls "
            "that permanently cap new housing supply. The result is one of the most consistently high-demand real estate markets in Southern California."
            "<br><br>"
            "Santa Monica's neighborhoods each have a distinct character. North of Montana is the city's most expensive pocket, "
            "averaging over $4.5M in sales. Sunset Park offers larger lots and more family-friendly pricing. "
            "Ocean Park brings an energetic Main Street lifestyle at a lower entry point. "
            "Downtown Santa Monica, anchored by the Third Street Promenade, appeals to buyers who prioritize urban walkability."
        ),
        "schools": [
            ("Franklin Elementary School", "Rated 9 out of 10, located in the North of Montana neighborhood."),
            ("Roosevelt Elementary School", "Another 9 out of 10 school, also serving the North of Montana area."),
            ("Santa Monica High School (Samohi)", "One of California's most well-known public high schools, serving all of Santa Monica."),
            ("Santa Monica-Malibu Unified School District", "A standalone district known for strong academics and arts programs."),
        ],
        "features": [
            "Pacific Ocean beach access and the Santa Monica Pier",
            "Strict city zoning limits new construction to under 200 units per year",
            "North of Montana: the city's most expensive neighborhood, averaging $4.5M+",
            "Standalone Santa Monica-Malibu Unified School District",
            "Third Street Promenade, Main Street, and Montana Avenue retail",
            "4.2 months of inventory as of early 2026, indicating a near-balanced market",
        ],
        "ben_note": (
            "Santa Monica requires a broker who understands the nuances of each sub-neighborhood. "
            "North of Montana, Sunset Park, Ocean Park, and Downtown Santa Monica each have distinct price drivers. "
            "Ben Lee's data-driven pricing approach and his reach into the Westside buyer pool mean Santa Monica "
            "sellers consistently attract qualified, motivated buyers."
        ),
        "faqs": [
            ("What is the median home price in Santa Monica?",
             "The median sale price for a single-family home in Santa Monica is approximately $3,850,000 as of January 2026. Condos and townhomes have a median closer to $1,250,000. The overall median including all property types sits near $1,565,000. Prices are projected to rise about 3.2% through the end of 2026."),
            ("What are the best neighborhoods in Santa Monica?",
             "North of Montana is Santa Monica's most exclusive neighborhood, with average sale prices exceeding $4.5M and top-rated elementary schools. Sunset Park offers more space and family-friendly lots. Ocean Park is popular for its proximity to Main Street. Downtown Santa Monica suits buyers who want walkability and urban energy."),
            ("What schools serve Santa Monica?",
             "Santa Monica has its own standalone Santa Monica-Malibu Unified School District. Franklin Elementary and Roosevelt Elementary (both 9/10) are in North of Montana. Santa Monica High School (Samohi) is one of California's most well-known public high schools."),
            ("Why is Santa Monica real estate so expensive?",
             "Santa Monica's strict zoning laws limit new construction to fewer than 200 units per year in a city already densely built. Combined with beach access, an excellent school district, and a globally recognized lifestyle, demand consistently outpaces supply. This structural undersupply is the primary driver of long-term price appreciation."),
            ("Does Ben Lee cover Santa Monica?",
             "Yes. Ben Lee Properties covers the full Westside including Santa Monica. Ben's extensive database of Westside buyers and his monthly newsletter distribution mean Santa Monica listings get immediate, targeted exposure. Contact Ben at (310) 704-6580 or ben@benleeproperties.com."),
        ],
    },
]

# ── Shared HTML components ────────────────────────────────────────────────────

NAVBAR = """    <div class="aside-menu">
      <div class="menu-inner">
        <div class="menu-nav">
          <div data-w-id="fde05b21-a6bc-38ed-9e6f-347dd9cc72e8" class="menu-close"><img src="../images/close_white_24dp.svg" loading="lazy" alt="" class="menu-close-icon"></div>
        </div>
        <div class="menu-content">
          <div class="menu-column-left">
            <div class="menu-office-wrap">
              <div class="office-block">
                <p class="menu-office-title">Beverly Hills Office</p>
                <p class="menu-office-address">9454 Wilshire Blvd, Beverly Hills, CA 90212</p>
              </div>
              <div class="office-block">
                <p class="menu-office-title">West Los Angeles Office</p>
                <p class="menu-office-address">11500 W Olympic Blvd, Los Angeles, CA 90064</p>
              </div>
              <div class="menu-office-contacts">
                <a href="mailto:ben@benleeproperties.com" class="menu-contact-link">ben@benleeproperties.com</a>
                <a href="tel:+13107046580" class="menu-contact-link">(310) 704-6580</a>
              </div>
            </div>
            <a href="../index.html" class="menu-brand w-inline-block"><img src="../images/alley-template-real-estates-vertical-logo-white.svg" loading="lazy" alt="Ben Lee Properties logo" class="menu-brand-logo"></a>
          </div>
          <div class="menu-column-right">
            <div class="menu-main-links">
              <a href="../index.html" class="menu-link w-inline-block"><p class="menu-link-paragraph">Home</p></a>
              <a href="../about.html" class="menu-link w-inline-block"><p class="menu-link-paragraph">About</p></a>
              <a href="../for-buyers-3.html" class="menu-link w-inline-block"><p class="menu-link-paragraph">For buyers</p></a>
              <a href="../cities.html" class="menu-link w-inline-block w--current"><p class="menu-link-paragraph">Cities</p></a>
              <a href="../for-sellers.html" class="menu-link w-inline-block"><p class="menu-link-paragraph">For sellers</p></a>
              <a href="../valuation.html" class="menu-link w-inline-block"><p class="menu-link-paragraph">Valuation</p></a>
              <a href="../blog.html" class="menu-link w-inline-block"><p class="menu-link-paragraph">Newsletter</p></a>
              <a href="../contact.html" class="menu-link w-inline-block"><p class="menu-link-paragraph">Contact</p></a>
            </div>
            <div class="menu-socials">
              <a href="https://www.instagram.com/benleerealestate" target="_blank" rel="noopener" class="menu-social-button w-inline-block"><svg class="social-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="24" height="24" aria-hidden="true"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg></a>
              <a href="https://www.linkedin.com/in/benlee" target="_blank" rel="noopener" class="menu-social-button w-inline-block"><svg class="social-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="24" height="24" aria-hidden="true"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg></a>
            </div>
          </div>
        </div>
      </div>
      <img src="../images/pexels-alexandr-podvalny-7599735_1pexels-alexandr-podvalny-7599735.avif" loading="lazy" alt="Hand with keys" class="menu-background-image">
      <div class="menu-background"></div>
    </div>
    <div data-animation="default" data-collapse="none" data-duration="400" data-easing="ease" data-easing2="ease" role="banner" class="navbar-2 w-nav">
      <div class="navbar-container-2">
        <div class="nav-left-2">
          <a href="../index.html" class="brand is-2nd w-nav-brand">
            <div class="text-block _2 name">BEN LEE</div>
            <img src="../images/the-agency-logo-white.png" loading="lazy" alt="The Agency" class="image-2" style="height:40px;width:auto;object-fit:contain;">
          </a>
        </div>
        <nav role="navigation" class="nav-menu-2 w-nav-menu">
          <a href="../index.html" class="nav-link-2 w-nav-link">Home</a>
          <div data-hover="false" data-delay="0" class="dropdown-4 w-dropdown">
            <div class="dropdown-toggle-2 w-dropdown-toggle">
              <div class="icon-4 w-icon-dropdown-toggle"></div>
              <div class="text-block-6">ALL PROPERTIES</div>
            </div>
            <nav class="dropdown-list-4 w-dropdown-list">
              <a href="../for-buyers-3.html" class="dropdown-link w-dropdown-link">LIVE LISTINGS</a>
              <a href="../ben-lee-sold-properties.html" class="dropdown-link-2 w-dropdown-link">RECENT TRANSACTIONS</a>
              <a href="../current-listings.html" class="dropdown-link w-dropdown-link">BUILT BY BEN</a>
            </nav>
          </div>
          <a href="../about.html" class="nav-link-2 w-nav-link">Our team</a>
          <a href="../valuation.html" class="nav-link-2 w-nav-link">Valuation</a>
          <a href="../blog.html" class="nav-link-2 w-nav-link">Newsletter</a>
          <a href="../social-media.html" class="nav-link-2 w-nav-link">Social Media</a>
          <a href="../testimonials.html" class="nav-link-2 w-nav-link">Testimonials</a>
          <a href="../contact.html" class="nav-link-2 w-nav-link">Contact</a>
        </nav>
        <div class="menu-button w-nav-button">
          <div class="menu-button-flex">
            <div class="menu-text-block">Menu</div>
            <div class="burger-icon in-menu-button">
              <div class="burger-icon-line"></div>
              <div class="burger-icon-line"></div>
              <div class="burger-icon-line"></div>
            </div>
          </div>
        </div>
      </div>
    </div>"""

FOOTER = """      <footer id="footer" class="footer blp-footer">
        <div class="blp-footer-inner">
          <div class="blp-footer-top">
            <div class="blp-footer-brand">
              <div class="blp-footer-name">Ben Lee</div>
              <div class="blp-footer-tagline">Real Estate</div>
            </div>
            <nav class="blp-footer-nav">
              <a href="../for-buyers-3.html" class="blp-footer-link">Buyer</a>
              <a href="../for-sellers.html" class="blp-footer-link">Seller</a>
              <a href="../about.html" class="blp-footer-link">About</a>
              <a href="../blog.html" class="blp-footer-link">Newsletter</a>
              <a href="../contact.html" class="blp-footer-link">Contact</a>
            </nav>
            <div class="blp-footer-social">
              <a href="https://www.instagram.com/benleerealestate" target="_blank" rel="noopener" class="blp-footer-social-link"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="22" height="22" aria-hidden="true"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg></a>
              <a href="https://www.linkedin.com/in/benlee" target="_blank" rel="noopener" class="blp-footer-social-link"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="22" height="22" aria-hidden="true"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg></a>
            </div>
          </div>
          <div class="blp-footer-bottom">
            <span class="blp-footer-copy">&copy; 2026 Ben Lee Properties. All rights reserved.</span>
            <div class="blp-footer-contact-info">
              <a href="tel:+13107046580" class="blp-footer-contact-link">(310) 704-6580</a>
              <a href="mailto:ben@benleeproperties.com" class="blp-footer-contact-link">ben@benleeproperties.com</a>
            </div>
          </div>
        </div>
      </footer>"""

FLOATING_BTNS = """    <div class="section-10">
      <div class="div-block-28">
        <a href="../contact.html" class="div-block-29 w-inline-block"><img width="45" height="45" alt="Contact" src="../images/pen.svg" loading="lazy" class="image-13"></a>
        <a href="tel:+13107046580" class="div-block-29 w-inline-block"><img width="45" height="45" alt="Call" src="../images/call-1.svg" loading="lazy" class="image-13"></a>
        <a href="mailto:ben@benleeproperties.com?subject=Email%20from%20website%20" class="div-block-29 right a w-inline-block"><img width="45" height="45" alt="Email" src="../images/email-1.svg" loading="lazy" class="image-13"></a>
      </div>
    </div>"""


def build_faq_schema(faqs):
    items = []
    for q, a in faqs:
        items.append(f"""      {{
        "@type": "Question",
        "name": "{q}",
        "acceptedAnswer": {{
          "@type": "Answer",
          "text": "{a}"
        }}
      }}""")
    return '[\n' + ',\n'.join(items) + '\n    ]'


def build_page(n):
    slug = n["slug"]
    canonical = f"https://www.benleeproperties.com/cities/{slug}"
    faq_schema = build_faq_schema(n["faqs"])

    schools_html = "\n".join(
        f'              <li><strong>{s[0]}:</strong> {s[1]}</li>'
        for s in n["schools"]
    )
    features_html = "\n".join(
        f'              <li>{f}</li>' for f in n["features"]
    )
    faq_html = ""
    for q, a in n["faqs"]:
        faq_html += f"""              <details class="city-faq-item">
                <summary class="city-faq-question">{q}</summary>
                <p class="city-faq-answer">{a}</p>
              </details>
"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{n["name"]} Real Estate | Ben Lee Properties</title>
  <meta name="description" content="{n["meta_desc"]}">
  <meta name="keywords" content="{n["name"]} real estate, {n["name"]} homes for sale, {n["name"]} realtor, {n["name"]} broker, Ben Lee Properties, Westside LA real estate">
  <meta name="robots" content="index, follow">
  <meta name="author" content="Ben Lee Properties">
  <link rel="canonical" href="{canonical}">

  <!-- Open Graph -->
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Ben Lee Properties">
  <meta property="og:title" content="{n["name"]} Real Estate | Ben Lee Properties">
  <meta property="og:description" content="{n["og_desc"]}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="https://www.benleeproperties.com/{n["hero_img"].lstrip('../')}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:locale" content="en_US">

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{n["name"]} Real Estate | Ben Lee Properties">
  <meta name="twitter:description" content="{n["og_desc"]}">
  <meta name="twitter:image" content="https://www.benleeproperties.com/{n["hero_img"].lstrip('../')}">

  <meta content="width=device-width, initial-scale=1" name="viewport">

  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Place",
    "name": "{n["name"]}, Los Angeles, CA",
    "description": "{n["meta_desc"]}",
    "address": {{
      "@type": "PostalAddress",
      "addressLocality": "{n["name"]}",
      "addressRegion": "CA",
      "postalCode": "{n["zip"]}",
      "addressCountry": "US"
    }},
    "geo": {{
      "@type": "GeoCoordinates",
      "latitude": {n["geo_lat"]},
      "longitude": {n["geo_lon"]}
    }},
    "url": "{canonical}"
  }}
  </script>
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": {faq_schema}
  }}
  </script>
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "RealEstateAgent",
    "name": "Ben Lee Properties",
    "url": "https://www.benleeproperties.com",
    "telephone": "+13107046580",
    "areaServed": {{
      "@type": "Place",
      "name": "{n["name"]}, Los Angeles, CA"
    }}
  }}
  </script>

  <link href="../css/normalize.css" rel="stylesheet" type="text/css">
  <link href="../css/webflow.css" rel="stylesheet" type="text/css">
  <link href="../css/ben-lee-properties.webflow.css" rel="stylesheet" type="text/css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <script type="text/javascript">!function(o,c){{var n=c.documentElement,t=" w-mod-";n.className+=t+"js",("ontouchstart"in o||o.DocumentTouch&&c instanceof DocumentTouch)&&(n.className+=t+"touch")}}(window,document);</script>
  <link href="../images/favicon.png" rel="shortcut icon" type="image/x-icon">
  <link href="../images/webclip.png" rel="apple-touch-icon">
  <style>
    .city-stats-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 2em;
      margin: 2em 0;
    }}
    .city-stat-card {{
      background: #fff;
      border-left: 4px solid #be591f;
      padding: 1.5em;
    }}
    .city-stat-value {{
      font-family: 'Montserrat', sans-serif;
      font-size: 2em;
      font-weight: 700;
      color: #0a223f;
      margin-bottom: 0.2em;
    }}
    .city-stat-label {{
      font-family: 'IBM Plex Sans', sans-serif;
      font-size: 0.85em;
      color: #666;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .city-content-grid {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 3em;
      align-items: start;
    }}
    .city-section-label {{
      font-family: 'Montserrat', sans-serif;
      font-size: 0.75em;
      font-weight: 700;
      letter-spacing: 0.15em;
      text-transform: uppercase;
      color: #be591f;
      margin-bottom: 0.5em;
    }}
    .city-body-text {{
      font-family: 'IBM Plex Sans', sans-serif;
      font-size: 1.05em;
      line-height: 1.75;
      color: #2c2c2c;
    }}
    .city-list {{
      font-family: 'IBM Plex Sans', sans-serif;
      font-size: 1em;
      line-height: 1.9;
      color: #2c2c2c;
      padding-left: 1.2em;
    }}
    .city-faq-item {{
      border-bottom: 1px solid #e0e0e0;
      padding: 1.2em 0;
    }}
    .city-faq-question {{
      font-family: 'Montserrat', sans-serif;
      font-size: 1em;
      font-weight: 600;
      color: #0a223f;
      cursor: pointer;
      list-style: none;
    }}
    .city-faq-question::-webkit-details-marker {{ display: none; }}
    .city-faq-question::before {{
      content: "+ ";
      color: #be591f;
      font-weight: 700;
    }}
    details[open] .city-faq-question::before {{
      content: "- ";
    }}
    .city-faq-answer {{
      font-family: 'IBM Plex Sans', sans-serif;
      font-size: 0.95em;
      line-height: 1.7;
      color: #444;
      margin-top: 0.75em;
      padding-left: 1.2em;
    }}
    .ben-callout {{
      background: #0a223f;
      color: #fff;
      padding: 2.5em;
      border-left: 5px solid #be591f;
    }}
    .ben-callout p {{
      font-family: 'IBM Plex Sans', sans-serif;
      font-size: 1.05em;
      line-height: 1.75;
      color: #e8edf3;
      margin-bottom: 1.2em;
    }}
    @media (max-width: 767px) {{
      .city-stats-grid {{ grid-template-columns: 1fr; }}
      .city-content-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="page-wrapper">
{NAVBAR}
    <div class="embed-code w-embed"><style>/* custom css */</style></div>
    <main class="main">

      <!-- Hero -->
      <section class="section overflow-hidden">
        <div class="page-hero hero-is-higher">
          <div class="hero-claim">
            <p style="opacity:1;color:#fff;font-family:Montserrat,sans-serif;font-size:0.85em;letter-spacing:0.2em;text-transform:uppercase;margin-bottom:0.5em;">Westside Neighborhoods</p>
            <h1 style="opacity:1" class="hero-heading">{n["name"]}</h1>
            <div class="hero-claim-background"></div>
          </div>
          <div class="hero-buttons-wrap">
            <a href="#about" class="hero-button w-inline-block" style="opacity:1">
              <p class="button-paragraph">Explore</p>
              <img src="../images/arrow_drop_down_white_24dp.svg" loading="lazy" width="24" alt="" class="hero-button-icon">
            </a>
          </div>
        </div>
        <img src="{n["hero_img"]}" loading="lazy" alt="{n["hero_img_alt"]}" class="cover-image-absolute">
        <div class="background-reveal"></div>
      </section>

      <!-- Market Stats -->
      <section class="section blue-background">
        <div class="container w-container">
          <div class="padding-8em">
            <p class="city-section-label" style="color:#be591f;">Market Snapshot</p>
            <h2 class="heading-sellers" style="color:#fff;">{n["name"]} Real Estate Market</h2>
            <div class="city-stats-grid">
              <div class="city-stat-card">
                <div class="city-stat-value">{n["median_price"]}</div>
                <div class="city-stat-label">Median Sale Price</div>
              </div>
              <div class="city-stat-card">
                <div class="city-stat-value">{n["avg_dom"]}</div>
                <div class="city-stat-label">Avg. Days on Market</div>
              </div>
              <div class="city-stat-card">
                <div class="city-stat-value" style="font-size:1.2em;">{n["price_trend"].title()}</div>
                <div class="city-stat-label">Price Trend</div>
              </div>
            </div>
            <p class="city-body-text" style="color:#c8d4e0;margin-top:1em;">{n["price_note"]}</p>
          </div>
        </div>
      </section>

      <!-- About + Features -->
      <section id="about" class="section grey-background">
        <div class="container w-container">
          <div class="padding-8em">
            <div class="city-content-grid">
              <div>
                <p class="city-section-label">About the Neighborhood</p>
                <h2 class="heading-sellers-process" style="opacity:1;">Living in {n["name"]}</h2>
                <p class="city-body-text">{n["about"]}</p>
              </div>
              <div>
                <p class="city-section-label">What Makes {n["name"]} Stand Out</p>
                <ul class="city-list">
{features_html}
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Schools -->
      <section class="section white-border-bottom">
        <div class="container w-container">
          <div class="padding-8em">
            <p class="city-section-label">Education</p>
            <h2 class="heading-sellers-process" style="opacity:1;">Schools Serving {n["name"]}</h2>
            <ul class="city-list">
{schools_html}
            </ul>
          </div>
        </div>
      </section>

      <!-- Ben Lee Callout -->
      <section class="section">
        <div class="container w-container">
          <div class="padding-8em">
            <div class="ben-callout">
              <p class="city-section-label" style="color:#be591f;">Your Agent in {n["name"]}</p>
              <h2 style="font-family:Montserrat,sans-serif;font-size:1.8em;font-weight:400;color:#fff;margin-bottom:0.8em;">Ben Lee | Broker, Attorney, Westside Specialist</h2>
              <p>{n["ben_note"]}</p>
              <p>Licensed California Broker (CalRE #01808926) and Attorney. Over $1 billion in closed transactions. Monthly newsletter reaching 9,000+ Westside households.</p>
              <div style="margin-top:1.5em;display:flex;gap:1em;flex-wrap:wrap;">
                <a href="../contact.html" class="button w-inline-block" style="display:inline-flex;align-items:center;">
                  <p class="button-paragraph">Get in Touch</p>
                  <img src="../images/arrow_right_white_24dp.svg" loading="lazy" alt="" class="button-arrow-right">
                  <div class="button-background"></div>
                </a>
                <a href="../valuation.html" class="button w-inline-block" style="display:inline-flex;align-items:center;">
                  <p class="button-paragraph">Free Valuation</p>
                  <img src="../images/arrow_right_white_24dp.svg" loading="lazy" alt="" class="button-arrow-right">
                  <div class="button-background"></div>
                </a>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- FAQ -->
      <section class="section grey-background">
        <div class="container w-container">
          <div class="padding-8em">
            <p class="city-section-label">Common Questions</p>
            <h2 class="heading-sellers-process" style="opacity:1;">{n["name"]} Real Estate FAQ</h2>
            <div style="max-width:800px;margin-top:2em;">
{faq_html}
            </div>
          </div>
        </div>
      </section>

      <!-- CTA -->
      <div class="inquiry-call-to-action">
        <div class="container w-container">
          <div class="footer-contact">
            <p class="footer-contact-title">Ready to buy or sell in {n["name"]}?</p>
            <a href="../contact.html" class="button w-inline-block">
              <p class="button-paragraph">Contact Ben Lee</p>
              <img src="../images/arrow_right_white_24dp.svg" loading="lazy" alt="" class="button-arrow-right">
              <div class="button-background dark-blue-color"></div>
            </a>
          </div>
        </div>
      </div>

{FOOTER}
    </main>
{FLOATING_BTNS}
  </div>
  <script src="https://d3e54v103j8qbb.cloudfront.net/js/jquery-3.5.1.min.dc5e7f18c8.js?site=68edca0dd75d0e01f9bfe38d" type="text/javascript" integrity="sha256-9/aliU8dGd2tb6OSsuzixeV4y/faTqgFtohetphbbj0=" crossorigin="anonymous"></script>
  <script src="../js/webflow.js" type="text/javascript"></script>
  <script src="../js/custom.js" type="text/javascript"></script>
</body>
</html>"""


for n in NEIGHBORHOODS:
    html = build_page(n)
    html = html.replace('../', '/')
    path = os.path.join(CITIES_DIR, f"{n['slug']}.html")
    with open(path, 'w') as f:
        f.write(html)
    print(f"  WROTE: cities/{n['slug']}.html")

print(f"\nDone. Generated {len(NEIGHBORHOODS)} city pages.")
