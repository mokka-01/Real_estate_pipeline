
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select link
from `real-estate-pipeline-503510`.`real_estate`.`stg_raw_listings`
where link is null



  
  
      
    ) dbt_internal_test