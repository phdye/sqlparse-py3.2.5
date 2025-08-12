EXEC SQL
    SELECT  first_name
      ,     last_name
      INTO  :firstName
      ,     :lastName
      FROM  employees
     WHERE  employee_id = :id;
