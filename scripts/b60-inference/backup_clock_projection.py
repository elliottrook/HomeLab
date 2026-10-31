"""Offline calendar projection of sanitized backup schedules, never admission.

No network, filesystem, subprocess or effects. The local timezone database is
an input dependency, not proof of the remote scheduler's timezone database or
ambiguous-hour policy. Enumerate possible folds; never guess which one fires.
"""
from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

EXPECTED = {1: '01:00', 3: '02:00', 2: '03:00'}


def project(rows, *, source_zone, day, contract_zone='America/Vancouver'):
    result = {'advisory_only': True, 'admission_granted': False,
              'status': 'invalid', 'tasks': []}
    try:
        calendar = date.fromisoformat(day)
        source, contract = ZoneInfo(source_zone), ZoneInfo(contract_zone)
        if not isinstance(rows, list):
            return result
        selected = [row for row in rows if isinstance(row, dict)
                    and type(row.get('id')) is int and row['id'] in EXPECTED]
        if len(selected) != 3 or {row['id'] for row in selected} != set(EXPECTED):
            return result
        aligned = True
        for row in sorted(selected, key=lambda r: EXPECTED[r['id']]):
            schedule = row.get('schedule', {})
            if (row.get('enabled') is not True or not isinstance(schedule, dict)
                    or any(schedule.get(key) != '*' for key in ('dom', 'month', 'dow'))):
                return result
            raw_hour, raw_minute = schedule.get('hour'), schedule.get('minute')
            if (not isinstance(raw_hour, str) or not raw_hour.isascii() or not raw_hour.isdigit()
                    or not isinstance(raw_minute, str) or not raw_minute.isascii()
                    or not raw_minute.isdigit()):
                return result
            hour, minute = int(raw_hour), int(raw_minute)
            naive = datetime(calendar.year, calendar.month, calendar.day, hour, minute)
            candidates = {}
            for fold in (0, 1):
                local = naive.replace(tzinfo=source, fold=fold)
                epoch = int(local.timestamp())
                # Round-trip rejects nonexistent spring-forward wall times.
                if datetime.fromtimestamp(epoch, source).replace(tzinfo=None) != naive:
                    continue
                candidates[epoch] = datetime.fromtimestamp(epoch, contract).isoformat()
            expected = datetime.combine(calendar, datetime.strptime(
                EXPECTED[row['id']], '%H:%M').time()).replace(tzinfo=contract)
            exact = list(sorted(candidates)) == [int(expected.timestamp())]
            aligned = aligned and exact
            result['tasks'].append({'id': row['id'], 'source_clock': f'{hour:02}:{minute:02}',
                'contract_expected': expected.isoformat(),
                'possible_contract_occurrences': [candidates[k] for k in sorted(candidates)],
                'ambiguous': len(candidates) > 1, 'nonexistent': not candidates,
                'exact_clock_match': exact})
        result['status'] = 'clock-aligned-not-qualified' if aligned else 'clock-mismatch'
    except (ValueError, TypeError, OverflowError, ZoneInfoNotFoundError):
        return result
    return result
