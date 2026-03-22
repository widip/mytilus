"""Mytilus-specific program-closed category package."""

import mytilus.pcc.loader as pcc_loader
import mytilus.pcc.mytilus as pcc_mytilus


LOADER = pcc_loader.LoaderLanguage()
SHELL = pcc_mytilus.ShellLanguage()
