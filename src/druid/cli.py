""" Command-line interface for druid """

import sys
import time

import click

import requests
import wget
import os

from druid import __version__
from druid.crow import Crow
from druid import repl as druid_repl
from druid import pydfu

@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(__version__)
def cli(ctx):
    """ Terminal interface for crow """
    if ctx.invoked_subcommand is None:
        ctx.invoke(repl)

@cli.command(short_help="Download a file from crow")
def download():
    """
    Download a file from crow and print it to stdout
    """
    with Crow() as crow:
        crow.connect()
        crow.write('^^p')
        time.sleep(0.3)
        click.echo(crow.read(1000000))

@cli.command(short_help="Upload a file to crow")
@click.argument("filename", type=click.Path(exists=True))
def upload(filename):
    """
    Upload a file to crow.
    FILENAME is the path to the Lua file to upload
    """
    with Crow() as crow:
        crow.connect()
        crow.upload(filename)
        click.echo(crow.read(1000000))
        time.sleep(0.3)
        crow.write('^^p')
        time.sleep(0.3)
        click.echo(crow.read(1000000))

@cli.command(short_help="Update bootloader")
def update():
    """ Update bootloader
    """
    print("Checking for updates...")
    git_query = requests.get('https://raw.githubusercontent.com/monome/crow/main/version.txt')
    git_data = git_query.text.split()
    print(">> git version", git_data[0])

    with Crow() as crow:
      local_version = "none"
      try:
        crow.connect()
      except:
        print("No crow found, or might be in bootloader mode already...")
        local_version = "0"

      # crow found: clear script and read version
      if local_version != "0":
        crow.write("^^c")
        time.sleep(1.0)
        c = crow.read(1000000)
        crow.write("^^v")
        tmp = (crow.read(100)).split("'")
        local_version = tmp[1][1:]

      print(">> local version: ", local_version)

      if local_version >= git_data[0]:
        print("Up to date.")
        exit()

      # delete old crow.dfu if exists
      if os.path.exists("crow.dfu"):
        os.remove("crow.dfu")

      print("Downloading new version:", git_data[1])
      wget.download(git_data[1])
      print("\n")

      if local_version != "0":
        crow.write('^^b')
        time.sleep(1.0)
        print("Crow bootloader enabled.")

      try:
        pydfu.init()
      except ValueError:
        print("Error: pydfu didn't find crow!")
        exit()

      elements = pydfu.read_dfu_file("crow.dfu")
      if not elements:
          return
      print("Writing memory...")
      pydfu.write_elements(elements, True, progress=pydfu.cli_progress)

      print("Exiting DFU...")
      pydfu.exit_dfu()

      os.remove("crow.dfu")
      print("Update complete.")


@cli.command()
@click.argument("filename", type=click.Path(exists=True), required=False)
def repl(filename):
    """ Start interactive terminal """
    druid_repl.main(filename)
