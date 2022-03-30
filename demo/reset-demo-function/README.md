# Reset PANW Splunk Demo

This GCP Function runs every week to reset the Splunk Demo running in the
kubernetes cluster. This reset is important to clear out any dashboard changes
made by demonstrators and to clear out the index so it doesn't fill the drive.

Use the included `Makefile` to perform common functions.

For example:

If you change a dependency in `pyproject.toml` or `poetry.lock`, use this
command to sync the dependency change to `requirements.txt`:

    $ make sync-deps

To deploy the function to GCP, create a `config.yml` file per the included
example and run:

    $ make deploy

Check for security vulnerabilities:

    $ make bandit

Check code formatting:

    $ make check-format

Format code:

    $ make format

See the help for more usage information:

    $ make help