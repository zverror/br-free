#!/usr/bin/env bash
set -Eeo pipefail

# A helper script which can create an empty database with a new user as specified by
# the environment variables POSTGRES_DATABASE, POSTGRES_USER and POSTGRES_PASSWORD.

docker_verify_minimum_env() {
  if [[ -z "$POSTGRES_USER" ]]; then
    echo "Must set POSTGRES_USER" 2>&1
    exit 1;
  fi
  if [[ -z "$POSTGRES_DB" ]]; then
    echo "Must set POSTGRES_DB" 2>&1
    exit 1;
  fi
  if [[ -z "$POSTGRES_PASSWORD" ]]; then
    echo "Must set POSTGRES_PASSWORD" 2>&1
    exit 1;
  fi
  if [[ -z "$PGDATA" ]]; then
    echo "Must set PGDATA" 2>&1
    exit 1;
  fi
	# check password first so we can output the warning before postgres
	# messes it up
	if [ "${#POSTGRES_PASSWORD}" -ge 100 ]; then
		cat >&2 <<-'EOWARN'
			WARNING: The supplied POSTGRES_PASSWORD is 100+ characters.
			  This will not work if used via PGPASSWORD with "psql".
			  https://www.postgresql.org/message-id/flat/E1Rqxp2-0004Qt-PL%40wrigleys.postgresql.org (BUG #6412)
			  https://github.com/docker-library/postgres/issues/507
		EOWARN
	fi
}

# Execute sql script
docker_process_sql() {
	local query_runner=( psql -v ON_ERROR_STOP=1 --no-password --no-psqlrc --dbname "$POSTGRES_DB" )
	"${query_runner[@]}" "$@"
}

# create initial database
# uses environment variables for input: POSTGRES_DB
docker_setup_db() {
	local dbAlreadyExists
	dbAlreadyExists="$(
		docker_process_sql --dbname postgres --set db="$POSTGRES_DB" --tuples-only <<-'EOSQL'
			SELECT 1 FROM pg_database WHERE datname = :'db' ;
		EOSQL
	)"
	if [ -z "$dbAlreadyExists" ]; then
		docker_process_sql --dbname postgres \
		  --set db="$POSTGRES_DB" \
		  --set pass="$POSTGRES_PASSWORD" \
		  --set user="$POSTGRES_USER" \
		  <<-'EOSQL'
			CREATE DATABASE :"db";
			create user :"user" with encrypted password :'pass';
			grant all privileges on database :"db" to :"user";
			alter database :"db" OWNER TO :"user";
		EOSQL
	fi
}

# start postgresql server for setting up or running scripts
docker_temp_server_start() {
	# internal start of server in order to allow setup using psql client
	PGUSER="${PGUSER:-$POSTGRES_USER}" \
	pg_ctlcluster "$POSTGRES_VERSION" main start -- -w -o "-c listen_addresses=''"
}

# stop postgresql server after done setting up user and running scripts
docker_temp_server_stop() {
	PGUSER="${PGUSER:-postgres}" \
	pg_ctlcluster "$POSTGRES_VERSION" main stop -- -m fast -w
}

_main() {
    export PGDATA="$DATA_DIR/postgres/"
    export POSTGRES_USER=$DATABASE_USER
    export POSTGRES_PASSWORD=$DATABASE_PASSWORD
    export POSTGRES_DB=$DATABASE_NAME

    export PGAUTOUPGRADE_DIR="${DATA_DIR}/pg_upgrade"

    ALREADY_SETUP_INDICATOR_FILE="$PGDATA/baserow_db_setup"

    # This script will re-run itself as postgres user, so this part is reserved for the root user setup/teardown
    if [ "$(id -u)" = '0' ]; then

      # The upgrade script will run as postgres user, so we need to create a directory
      # where the postgres user can write to.
      if [ "$1" == "upgrade" ] && [ ! -d ${PGAUTOUPGRADE_DIR} ]; then
        mkdir -p "${PGAUTOUPGRADE_DIR}"
        chown postgres:postgres "${PGAUTOUPGRADE_DIR}"
      fi

      # restart script as postgres user
      echo "Becoming postgres superuser to run setup SQL commands:"
      su postgres -c "${BASH_SOURCE[0]} $*"
      EXIT_STATUS=$?

      # If the upgrade script was run, and it was successful, remove the upgrade directory.
      if [ "$1" == "upgrade" ]; then
        if [ $EXIT_STATUS = 0 ]; then
          rm -rf "${PGAUTOUPGRADE_DIR}"
          echo
          echo 'You can now run the official `baserow/baserow:1.30.1` image to start Baserow.'
          echo
          # We want to stop the execution here, so return an error code even if the upgrade was successful.
          exit 1
        else
          exit $EXIT_STATUS
        fi
      fi
    # this part is reserved for the postgres user
    elif [ "$1" == "upgrade" ]; then
      if [ ! -f "$ALREADY_SETUP_INDICATOR_FILE" ]; then
          echo
          echo 'PostgreSQL Database directory does not contain a database; Skipping upgrade'
          echo
          exit 0
      fi

      # Get the current data version from the PG_VERSION file (https://www.postgresql.org/docs/current/storage-file-layout.html)
      PGDATA_VERSION=$(cat "${PGDATA}/PG_VERSION")

      if [ "$PGDATA_VERSION" = "$POSTGRES_VERSION" ]; then
        echo
        echo "Your PostgreSQL data directory is already at version $PGDATA_VERSION."
        echo
        exit 0
      fi

      echo
      echo "Your PostgreSQL data directory was initialized with version $PGDATA_VERSION, but this image is running version $POSTGRES_VERSION."
      echo

      if [ "$PGDATA_VERSION" = $POSTGRES_OLD_VERSION ]; then
        echo
        echo "Upgrading PostgreSQL data directory to version ${POSTGRES_VERSION}..."
        echo

        set +e

        ./docker-postgres-upgrade.sh
        UPGRADE_EXIT_STATUS=$?

        set -e

        if [ $UPGRADE_EXIT_STATUS -ne 0 ]; then
          echo
          echo "Upgrading to PostgreSQL ${POSTGRES_VERSION} failed with exit code ${UPGRADE_EXIT_STATUS}"
          echo
          exit 1
        else
          echo
          echo '...PostgreSQL data directory upgrade complete.'
          echo
        fi
      else
        echo
        echo "Your PostgreSQL data directory is at version $PGDATA_VERSION, which cannot be upgraded automatically."
        echo "Please look into Baserow official documentation for more information on how to upgrade your database."
        echo
        exit 1
      fi

    elif [ "$1" == "setup" ]; then
      shift

      if [ -f "$ALREADY_SETUP_INDICATOR_FILE" ]; then
        echo
        echo 'PostgreSQL Database directory appears to contain a database; Skipping initialization'
        echo

        # Get the current data version from the PG_VERSION file (https://www.postgresql.org/docs/current/storage-file-layout.html)
        PGDATA_VERSION=$(cat "${PGDATA}/PG_VERSION")

        if [ "$PGDATA_VERSION" != "$POSTGRES_VERSION" ]; then
          echo
          echo "Your PostgreSQL data directory was initialized with version $PGDATA_VERSION, but this image is running version $POSTGRES_VERSION."
          echo "Please look into official Baserow documentation at https://baserow.io/docs/installation%2Finstall-with-docker#upgrading-postgresql-database-from-a-previous-version for more information on how to upgrade your database using a different Baserow image ('baserow/baserow-pgautoupgrade:1.30.1') or how to run Baserow using legacy PostgreSQL 11 image ('baserow/baserow-pg11:1.30.1')."
          echo
          exit 1
        fi
      else
        docker_verify_minimum_env

        cp -pR "/var/lib/postgresql/$POSTGRES_VERSION/main/." "$DATA_DIR/postgres/"
        docker_temp_server_start "$@"
        docker_setup_db
        touch "$ALREADY_SETUP_INDICATOR_FILE"
        docker_temp_server_stop

        echo
        echo 'PostgreSQL init process complete; ready for start up.'
        echo
      fi
    elif [ "$1" == "run" ]; then
      shift
      if [[ $(pgrep -f "bin/postgres") ]]; then
        echo "PostgreSQL is already running. Directly running SQL."
        docker_process_sql "$@"
      else
        echo "No running postgresql found, starting one up..."
        docker_temp_server_start
        docker_process_sql "$@"
        docker_temp_server_stop
      fi
    else
      echo "Unknown argument $1 it must be either 'setup', 'upgrade' or 'run ...'"
      exit 1
    fi
}

_main "$@"
