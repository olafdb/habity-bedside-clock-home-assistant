# Habity Bedside Clock — Home Assistant Integration

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2023.1%2B-blue.svg)](https://www.home-assistant.io)

A Home Assistant integration for the [Habity Bedside Clock](https://habity.com), exposing alarm time and button presses via local HTTP & UDP.

---

## Features

- 📡 Local polling — no cloud, no account required
- 🕐 Exposes next alarm time
- ⚡ Instant button press update

---

## Requirements

- Home Assistant 2023.1 or newer
- Habity Bedside Clock connected to your local network

---

## Installation

### Via HACS (recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations** → **⋮** → **Custom repositories**
3. Add this repository URL and select **Integration**
4. Search for **Habity** and install it
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/habity` folder into your `config/custom_components/` directory
2. Restart Home Assistant

---

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Habity**
3. Enter the IP address of your clock
4. Done

---
