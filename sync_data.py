import argparse
from database import init_db, rows
from services.sync import (
    sync_team_school_site, sync_tds_rankings, sync_ncaa_leaders,
    sync_tds_extended, sync_registry, sync_ncaa_stat_tables,
    sync_ncaa_game_history, sync_registered_school_schedules, sync_ncaa_rankings,
)
from services.news import sync_news


def main():
    init_db()
    parser = argparse.ArgumentParser(description='College XI verified public-source sync')
    parser.add_argument('--team')
    parser.add_argument('--all', action='store_true')
    parser.add_argument('--rankings', action='store_true')
    parser.add_argument('--registry', action='store_true')
    parser.add_argument('--news', action='store_true')
    parser.add_argument('--games', action='store_true', help='sync 2026 game history for the selected world')
    parser.add_argument('--start-date', default='2026-08-01')
    parser.add_argument('--end-date', default='2026-12-31')
    parser.add_argument('--division', choices=['D1','D2','D3','NAIA','NJCAA1'], default='D1')
    args = parser.parse_args()

    if args.registry or args.all:
        if args.division == 'D1':
            r = sync_registry()
            print('D1 registry:', {'ok': r.get('ok'), 'teams': len(r.get('items', [])), 'error': r.get('error')})
        else:
            print('Registry: no verified global registry adapter is configured for', args.division)

    if args.games or args.all:
        if args.division in ('D1','D2','D3'):
            print('Game history:', sync_ncaa_game_history(args.division, args.start_date, args.end_date))
        else:
            print('Official registered schedules:', sync_registered_school_schedules(args.division))

    if args.rankings or args.all:
        if args.division in ('D1','D2','D3'):
            print('NCAA rankings:', sync_ncaa_rankings(args.division))
            print('NCAA stat tables:', sync_ncaa_stat_tables(args.division))
        if args.division == 'D1':
            print('TDS:', sync_tds_rankings())
            print('TDS extended:', sync_tds_extended())
            print('NCAA leaders:', sync_ncaa_leaders())

    if args.news or args.all:
        print('News:', sync_news(args.division))

    if args.team:
        print(sync_team_school_site(args.team))
    elif args.all and args.division == 'D1':
        teams = rows("SELECT school FROM teams WHERE division='D1' AND (official_url IS NOT NULL OR roster_url IS NOT NULL) ORDER BY school")
        ok, failed = 0, []
        for i, t in enumerate(teams, 1):
            school = t['school']
            print(f'[{i}/{len(teams)}] {school}')
            try:
                print(' ', sync_team_school_site(school)); ok += 1
            except Exception as exc:
                print('  FAILED:', exc); failed.append((school, str(exc)))
        print(f'Complete: {ok}; failed: {len(failed)}')
        for school, err in failed:
            print(' -', school, '->', err)


if __name__ == '__main__':
    main()
