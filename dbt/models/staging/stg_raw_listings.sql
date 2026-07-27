-- Cleans raw scraped listing data into proper types.
-- Source: raw_listings (loaded as-is from Postgres, untouched, still there
-- if this logic ever needs to change and be re-run).

with source as (
    select * from `{{ target.project }}`.`{{ target.dataset }}`.raw_listings
)

select
    id,
    title,
    address,
    link,
    scraped_at,

    -- Price format from source: "128 990 €" (space thousands separator, no decimals)
    -- Strip everything except digits, then cast to a whole number.
    safe_cast(
        regexp_replace(price_eur, r'[^0-9]', '')
        as int64
    ) as price_eur,

    -- price_per_sqm format: "3307,44 €/m²" (comma as DECIMAL separator here,
    -- unlike price_eur above -- a real inconsistency in the source data).
    safe_cast(
        regexp_replace(replace(price_per_sqm, ',', '.'), r'[^0-9.]', '')
        as numeric
    ) as price_per_sqm,

    -- area_sqm format: "56.9 m²" (period decimal, already consistent -- no
    -- comma-to-period conversion needed here, unlike price_per_sqm above).
    safe_cast(
        regexp_replace(area_sqm, r'[^0-9.]', '')
        as numeric
    ) as area_sqm,

    -- rooms format: "2 camere" / "1 cameră" -- extract the leading digit.
    safe_cast(
        regexp_extract(rooms, r'^(\d+)')
        as int64
    ) as room_count,

    -- floor format: "etajul 10" (extract digit) OR "parter" (ground floor,
    -- non-numeric -- a real edge case worth handling explicitly rather than
    -- letting it silently become NULL).
    case
        when lower(floor) = 'parter' then 0
        else safe_cast(regexp_extract(floor, r'(\d+)') as int64)
    end as floor_number,
     -- extract sector number from address, e.g. "Sectorul 3, Bucuresti" -> 3
    safe_cast(
        regexp_extract(address, r'Sectorul (\d+)')
        as int64
    ) as sector

from source
