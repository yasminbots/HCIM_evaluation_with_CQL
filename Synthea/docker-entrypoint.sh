#!/bin/bash

CLEAR_TESTDATA_DIRS=${CLEAR_TESTDATA_DIRS:-"true"}

# PROCESSING FILES
ENABLE_PROCESS_TESTDATA=${ENABLE_PROCESS_TESTDATA:-""}
TIMEOUT=${TIMEOUT:-1}
GZIP_PROCESSED_OUTPUT_FILES=${GZIP_PROCESSED_OUTPUT_FILES:-"false"}
REMOVE_INPUTFILES_PROCESSING=${REMOVE_INPUTFILES_PROCESSING:-"false"}
RELEVANT_RESOURCES=${RELEVANT_RESOURCES:-"Patient,Encounter,Observation,Condition,DiagnosticReport,Medication,MedicationAdministration,Procedure"}

# SENDING TO FHIR
ENABLE_SENT_DATA_TO_FHIR=${ENABLE_SENT_DATA_TO_FHIR:-""}
GZIPPED_FHIR_SEND_INPUT_FILES=${GZIPPED_FHIR_SEND_INPUT_FILES:-"false"}
REMOVE_INPUTFILES_FHIR_SENDING=${REMOVE_INPUTFILES_FHIR_SENDING:-"false"}
FHIR_URL=${FHIR_URL:-"http://fhir-server:8080/fhir"}
FHIR_USER=${FHIR_USER:-""}
FHIR_PW=${FHIR_PW:-""}

# SYNTHEA GENERATION
ENABLE_GENERATE_SYNTHEA_DATA=${ENABLE_GENERATE_SYNTHEA_DATA:-""}
N_PATIENTS=${N_PATIENTS:-100}
SEED=${SEED:-"3256262546"}
CLINICIAN_SEED=${CLINICIAN_SEED:-"3726451"}

if [ "$CLEAR_TESTDATA_DIRS" = "true" ]; then
   printf "## Removing previously generated data... \n\n"
   rm -rf output/*

   mkdir -p output/fhir-processed
   mkdir -p output/metadata
fi

if [ "$ENABLE_PROCESS_TESTDATA" = "true" ]; then
   printf "\n## Starting continuous post-processing of synthea data...\n"

   if [ "$ENABLE_GENERATE_SYNTHEA_DATA" = "true" ] || [ "$ENABLE_SENT_DATA_TO_FHIR" = "true" ]; then
      printf "### Synthea generation or Sending data to FHIR enabled => starting in background... \n"
      python3 -u testdata-post-processing.py --log-level info --metadatadir output/metadata --inputdir output/fhir --outputdir output/fhir-processed\
      --timeout $TIMEOUT --gzipfiles $GZIP_PROCESSED_OUTPUT_FILES --removeinputfiles $REMOVE_INPUTFILES_PROCESSING\
      --relevant-resources $RELEVANT_RESOURCES &
   else
      printf "### Only processing of testdata enabled => starting in foreground... \n"
      python3 -u testdata-post-processing.py --log-level info --metadatadir output/metadata --inputdir output/fhir --outputdir output/fhir-processed\
      --timeout $TIMEOUT --gzipfiles $GZIP_PROCESSED_OUTPUT_FILES --removeinputfiles $REMOVE_INPUTFILES_PROCESSING\
      --relevant-resources $RELEVANT_RESOURCES
   fi
fi

if [ "$ENABLE_SENT_DATA_TO_FHIR" = "true" ]; then
   printf "\n## Starting continuous loading of data into a FHIR server ...\n"

   if [ "$ENABLE_GENERATE_SYNTHEA_DATA" = "true" ]; then
      printf "### Synthea generation enabled => starting in background... \n\n"
      python3 -u continuously-load-testdata.py --log-level info --metadatadir output/metadata --inputdir output/fhir-processed\
      --timeout $TIMEOUT --removeinputfiles $REMOVE_INPUTFILES_FHIR_SENDING\
      --gzippedfiles $GZIPPED_FHIR_SEND_INPUT_FILES --fhirurl $FHIR_URL --fhiruser $FHIR_USER --fhirpw $FHIR_PW &
   else
      printf "### Synthea generation disabled => starting in foreground... \n\n"
      python3 -u continuously-load-testdata.py --log-level info --metadatadir output/metadata --inputdir output/fhir-processed\
      --timeout $TIMEOUT --removeinputfiles $REMOVE_INPUTFILES_FHIR_SENDING\
      --gzippedfiles $GZIPPED_FHIR_SEND_INPUT_FILES --fhirurl $FHIR_URL --fhiruser $FHIR_USER --fhirpw $FHIR_PW
   fi
fi

if [ "$ENABLE_GENERATE_SYNTHEA_DATA" = "true" ]; then
   printf "## Starting synthea data generation - Generating %s patients with SEED: %s and CLINICIAN_SEED: %s\n\n" "$N_PATIENTS" "$SEED" "$CLINICIAN_SEED"
   java -jar synthea.jar -s "$SEED" -cs "$CLINICIAN_SEED" -r "20210101" -a "0-100" -c "synthea.properties" -p $N_PATIENTS
fi

printf "## Waiting twice timeout = $TIMEOUT in minutes for background processes to finish \n\n"
sleep "$(($TIMEOUT * 60 * 2))"