
    
    

with dbt_test__target as (

  select link as unique_field
  from `real-estate-pipeline-503510`.`real_estate`.`stg_raw_listings`
  where link is not null

)

select
    unique_field,
    count(*) as n_records

from dbt_test__target
group by unique_field
having count(*) > 1


