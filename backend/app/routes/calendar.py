"""
Calendar routes for Badí' (Bahá'í) calendar functionality.
"""

from flask import Blueprint, jsonify, request
from datetime import date
from app.utils.badi_calendar import (
    gregorian_to_badi,
    badi_to_gregorian,
    get_badi_month_date_range,
    get_badi_year_date_range,
    get_current_badi_date,
    get_all_months,
    get_badi_month_name,
    format_badi_date,
    gregorian_year_to_badi_year
)

bp = Blueprint('calendar', __name__, url_prefix='/api/calendar')

@bp.route('/badi/months', methods=['GET'])
def get_badi_months():
    """Get all Badí' months with their names and meanings."""
    return jsonify(get_all_months())

@bp.route('/badi/current', methods=['GET'])
def get_current_date():
    """Get the current date in Badí' calendar."""
    year, month, day = get_current_badi_date()
    month_info = get_badi_month_name(month)
    
    return jsonify({
        'year': year,
        'month': month,
        'day': day,
        'month_info': month_info,
        'formatted': format_badi_date(year, month, day)
    })

@bp.route('/badi/convert/from-gregorian', methods=['GET'])
def convert_from_gregorian():
    """Convert a Gregorian date to Badí' date."""
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    day = request.args.get('day', type=int)
    
    if not all([year, month, day]):
        return jsonify({'error': 'Missing required parameters: year, month, day'}), 400
    
    try:
        gregorian_date = date(year, month, day)
        badi_year, badi_month, badi_day = gregorian_to_badi(gregorian_date)
        month_info = get_badi_month_name(badi_month)
        
        return jsonify({
            'year': badi_year,
            'month': badi_month,
            'day': badi_day,
            'month_info': month_info,
            'formatted': format_badi_date(badi_year, badi_month, badi_day)
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/badi/convert/to-gregorian', methods=['GET'])
def convert_to_gregorian():
    """Convert a Badí' date to Gregorian date."""
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    day = request.args.get('day', type=int)
    
    if year is None or month is None or day is None:
        return jsonify({'error': 'Missing required parameters: year, month, day'}), 400
    
    try:
        gregorian_date = badi_to_gregorian(year, month, day)
        
        return jsonify({
            'year': gregorian_date.year,
            'month': gregorian_date.month,
            'day': gregorian_date.day,
            'formatted': gregorian_date.strftime('%Y-%m-%d')
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/badi/date-range', methods=['GET'])
def get_date_range():
    """Get the Gregorian date range for a Badí' month or year."""
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)  # Optional
    
    if year is None:
        return jsonify({'error': 'Missing required parameter: year'}), 400
    
    try:
        if month is not None:
            start, end = get_badi_month_date_range(year, month)
            month_info = get_badi_month_name(month)
        else:
            start, end = get_badi_year_date_range(year)
            month_info = None
        
        return jsonify({
            'start': start.strftime('%Y-%m-%d'),
            'end': end.strftime('%Y-%m-%d'),
            'badi_year': year,
            'badi_month': month,
            'month_info': month_info
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/badi/years', methods=['GET'])
def get_available_years():
    """Get available Badí' years based on current date."""
    current_year, _, _ = get_current_badi_date()
    
    # Return years from 5 years ago to current year
    years = list(range(current_year - 5, current_year + 1))
    
    return jsonify({
        'current_year': current_year,
        'years': years
    })

@bp.route('/gregorian/year-to-badi', methods=['GET'])
def gregorian_year_to_badi():
    """Convert a Gregorian year to a Badí' year."""
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int, default=1)
    
    if year is None:
        return jsonify({'error': 'Missing required parameter: year'}), 400
    
    badi_year = gregorian_year_to_badi_year(year, month)
    
    return jsonify({
        'gregorian_year': year,
        'gregorian_month': month,
        'badi_year': badi_year
    })
