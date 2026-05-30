# AirInk HandConsole Adapter

This directory contains a new, isolated refactor track for adapting AirInk to the HandConsole development framework.

## Scope

This adapter does not modify the existing AirInk Python/PySide6 implementation and does not modify HandConsole.

All new work is kept under:

```text
handconsole_adapter/
```

## Goal

Reorganize AirInk as a HandConsole-style desktop module based on:

- Tauri 2 backend
- React + TypeScript frontend
- Vite development server
- React Router page routing
- Zustand state stores
- Tauri commands and event streams

## Target capabilities

- Camera status and preview pipeline
- Hand tracking frame stream
- Pinch-based pen down/up state machine
- Writing canvas and stroke session model
- Active-region calibration
- Recognition provider contract
- Session recording and playback
- Future integration into HandConsole as an AirInk module

## Non-goals for this adapter stage

- Replacing the current AirInk implementation
- Changing HandConsole navigation or backend modules
- Moving existing AirInk files
- Deleting or rewriting existing source code

## Current stage

Phase 0 / Phase 1 scaffold.

The initial files define the architecture, integration contract, migration plan, and a minimal desktop adapter skeleton.
