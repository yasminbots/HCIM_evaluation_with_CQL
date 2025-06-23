# Installation
In this test setup, CQF ruler and Synthea will be deployed in Docker, and Postman is used to test against the FHIR endpoint created by CQF ruler.
For the two containers to work together, a network is defined in the environment. Containers CQF ruler and Synthea expect a network named web. 
Make sure to create a network named web before deploying the containers.
`docker network create web`

Check if web is created.
`docker network ls`

And check if both containers are running on web.
`docker inspect web`

Install CQF ruler and Synthea containers and deploy in Docker. The FHIR server should be locally available at port 8080, check if this is the case. 
`docker ps`
It should be available in the browser at http://localhost:8080/fhir/swagger-ui/

Generate enough data with Synthea for tests to be useful. The number of patients generated is set to 10, and can be altered in the environment file. 
See if the data is present at the FHIR server http://localhost:8080/fhir/Patient

# Run CQL
Use the provided Postman collection to run CQL libraries. For a connection with the Dutch Terminology Server, https://nictiz.nl/app/uploads/2024/07/NTS-Handleiding-voor-nieuwe-gebruikers-12-03-2024.pdf?_gl=1*fzu5h6*_up*MQ..*_ga*MjA1ODk2Nzc2NS4xNzUwNjgzMzY3*_ga_0ZRXV90GXH*czE3NTA2ODMzNjYkbzEkZzEkdDE3NTA2ODMzNzYkajUwJGwwJGgyMDQzNzMyMTEy.
The username and password should be filled in by the variables of the Postman collection if the Dutch Terminology Server is needed for the execution of CQL scripts.
The collection contains some CQL libraries, providing minimal working examples.
