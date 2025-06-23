# PrivateAIM FHIR Test Data Populator

Based on the [mii-testdata](https://github.com/medizininformatik-initiative/mii-testdata) repository.

This repository provides the functionality to generate [Synthea](https://github.com/synthetichealth/synthea) test data and subsequently load this data into a FHIR server.

## Usage

To create a test dataset, first configure the environment variables in the .env file. More details are provided in the section below.

Next, run the command `docker-compose up -d` to execute the Docker image and wait for the container to complete its process.

You can monitor the logs and the current status of the data-generating container by using the command `docker-compose logs -f`.

The container will produce FHIR data based on the settings in the synthea.properties file.

Please note: If you're sending data to a FHIR server within your Docker network, make sure the containers are connected to the same network.

## Environment Variables

| EnvVar | Description | Default |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| CLEAR_TESTDATA_DIRS | Enables clearing of the testdata dirs. Possible Values: true,   false | true |
| ENABLE_GENERATE_SYNTHEA_DATA | Enables the generation of   the synthea data - enable if no data has been generated yet or if you want to   generate new data. Possible Values: true, false | true |
| SYNTHEA_N_PATIENTS | The number of patients you would like to generate data for | 100 |
| SYNTHEA_SEED | The seed (-s) for the synthea tool | 3256262546 |
| SYNTHEA_CLINICIAN_SEED | The clinicianSeed (-cs) for the synthea tool | 3726451 |
| TIMEOUT | The time the processing and sending programs wait for new files to appear before they shut down. This is used to continuously process the synthea data as it is being generated. |  |
| ENABLE_PROCESS_TESTDATA | Enables the post processing of the synthea data. Possible Values: true, false |  |
| GZIP_PROCESSED_OUTPUT_FILES | Would you like to gzip the processed files to save disk space? Possible Values: true, false |  |
| REMOVE_INPUTFILES_PROCESSING | Should the input files be removed after processing to save disk space? Possible Values: true, false |  |
| RELEVANT_RESOURCES | Comma separated list of FHIR resourceTypes of a Bundle which should be kept |  |
| ENABLE_SENT_DATA_TO_FHIR | Enables the loading of the data directly into the FHIR sever. Possible Values: true, false |  |
| GZIPPED_FHIR_SEND_INPUT_FILES | Are your input files you are sending gzipped? Possible Values: true, false |  |
| REMOVE_INPUTFILES_FHIR_SENDING | Should the input files be removed after sending it to the FHIR server to save disk space? Possible Values: true, false |  |
| FHIR_URL | base url of the FHIR server. Possible Values: string - commonly base urls end with /fhir |  |
| FHIR_USER | basic auth user for FHIR server if used |  |
| FHIR_PW | basic auth password for FHIR server if used |  |
