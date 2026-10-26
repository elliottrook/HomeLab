# Static function-only fixture; never invoke against a host.
# Original module SHA-256: 9efe6e5dc1aafdbbff5c7caa2af390a31c9b1c9935220243cd371023cb21e8a1
def final(runner: Callable, *, popen=subprocess.run,
          clock: Callable[[], float] = time.time) -> dict:
    """Run one fresh final gate and the existing bounded observer once."""
    epoch = int(clock())
    cycle, minute = _cycle(epoch)
    try:
        if minute != FINAL_MINUTE:
            raise ScheduledF2Error("final gate is outside the 01:20 window")
        if _existing_state(cycle) != {"schema": SCHEMA, "cycle": cycle,
                                      "phase": "prepare", "state": "prepared",
                                      "error_class": "", "first_failure_phase": "",
                                      "failure_class": ""}:
            raise ScheduledF2Error("prepared state is absent or not exact")
        try:
            run_fixed_final_guard(runner)
        except F2FinalGuardError as exc:
            raise FinalSubcheckError(exc.code, "final guard subcheck failed") from exc
        except Exception as exc:
            raise FinalSubcheckError("FINAL_GUARD_SUBCHECK_FAILED",
                                     "final guard subcheck failed") from exc
        local = datetime.fromtimestamp(epoch, LOCAL_ZONE)
        hard_end = local.replace(hour=1, minute=40, second=0, microsecond=0).timestamp()
        timeout = max(1, int(hard_end - epoch))
        try:
            process = popen(("/usr/bin/python3", "-B", str(OBSERVER), "--read-only-authorized"),
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                            start_new_session=True,
                            env={"PATH": "/usr/bin:/bin", "PYTHONPATH": str(OBSERVER.parent),
                                 "PYTHONDONTWRITEBYTECODE": "1", "LANG": "C"})
        except Exception as exc:
            raise FinalSubcheckError("OBSERVER_LAUNCH_FAILED",
                                     "bounded observer launch failed") from exc
        try:
            output, _ = process.communicate(timeout=max(1, timeout - 5))
        except subprocess.TimeoutExpired as exc:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.communicate(timeout=5)
            raise ScheduledF2Error("bounded observer reached hard deadline") from exc
        except Exception as exc:
            raise FinalSubcheckError("OBSERVER_COMMUNICATION_FAILED",
                                     "bounded observer communication failed") from exc
        if process.returncode != 0:
            raise FinalSubcheckError("OBSERVER_EXIT_NONZERO",
                                     "bounded observer returned no-go")
        if len(output) > 8_192:
            raise ScheduledF2Error("bounded observer projection is oversized")
        try:
            projection = json.loads(output.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ScheduledF2Error("bounded observer projection is invalid") from exc
        _validate_projection(projection, cycle)
        value = {"schema": SCHEMA, "cycle": cycle, "phase": "final", "state": "complete",
                 "result": projection}
        _write_state(cycle, "final", "complete", result=projection)
        return value
    except Exception as exc:
        try:
            _record_failure(cycle, "final", exc)
        except Exception:
            pass
        raise
