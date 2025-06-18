# cqf-ruler

These files can be used to create a docker container with CQFRuler and a postgress database. All depedencies are installed as well. This is only setup for testing purposes, do not use this with senstive data in a live environment.

The cqf-ruler is based on the HAPI FHIR JPA Server Starter and adds a set of plugins that provide an implementation of [FHIR's Clinical Reasoning Module](https://hl7.org/fhir/clinicalreasoning-module.html), serve as a knowledge artifact repository, and a cds-hooks compatible clinical decision support service. 

See the [wiki](https://github.com/cqframework/cqf-ruler/wiki) for more information



## Pre requisits
[Docker](https://www.docker.com/) or Docker Desktop

## Install
Run the following command from docker on the file location where these files are stored:

    Docker compose up

The cqf-ruler fhir api (Swagger) can be found on [localhost:8080/fhir](http://localhost:8080/fhir)

## License

Copyright 2025+ Nictiz

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.