
# Installation
Install CQF ruler and Synthea contianers and deploy in Docker. The FHIR server should be locally available at port 8080, check if this is the case. 
'docker ps'

Both containers should be on the same network. Right now, the containers expect a network named web to be there.
Create web with 
docker network create web

Check if web is created
docker network ls

And check if the containers are running on this network
docker inspect web

Generate enough data with synthea for tests to be useful. The amount of patients generated is set to 10, and can be altered in the environment file. 


docker ps (gives the running containers, including their ports)
docker network ls (what networks are there)
docker network create [name_network] (create a new network)
docker inspect [name_network] (inspect a network)

#Run CQL
Use the provided Postman collection to run CQL libraries. For a connction with the Dutch Terminology Server, ...   
