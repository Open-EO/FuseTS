#!/usr/bin/env groovy

// This Jenkinsfile is used to provide snapshot builds using the VITO CI system.

@Library('lib')_

pythonPipeline {
  package_name = 'fusets'
  wipeout_workspace = true
  python_version = ["3.11"]
  extras_require = 'dev'
  upload_dev_wheels = true
  enable_caching = true
  enable_uv = true
  artifactory_server = 'sas'
  wheel_repo = 'openeo-pypi-local'
  wheel_repo_dev = 'openeo-pypi-local'
}
