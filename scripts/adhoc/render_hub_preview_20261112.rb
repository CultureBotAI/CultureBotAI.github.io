#!/usr/bin/env ruby
# Purpose: Render the current hub body using installed Kramdown for browser QA.
# Inputs: mechs.md; output: supplied HTML fragment path (no Jekyll build).
# Serves: November 12 combined refresh PR. Date: 2026-11-12.
require 'kramdown'
source = File.read(ARGV.fetch(0)).sub(/\A---\n.*?\n---\n/m, '')
File.write(ARGV.fetch(1), Kramdown::Document.new(source).to_html)
