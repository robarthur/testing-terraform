import os
import pytest


@pytest.fixture(scope='session')
def terraform_dir():
  return os.path.join(os.path.dirname(os.path.abspath(__file__)), '../')
