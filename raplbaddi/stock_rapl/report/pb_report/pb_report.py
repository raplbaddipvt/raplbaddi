# Copyright (c) 2023, Nishant Bhickta and contributors
# For license information, please see license.txt

import frappe
from frappe.query_builder import DocType
from frappe.query_builder.functions import Concat, Sum, GroupConcat, Coalesce
from frappe.utils import get_url
from raplbaddi.utils import report_utils
from raplbaddi.stock_rapl.report.pb_report.box_data import BoxRequirements

box_data = BoxRequirements()

def execute(filters=None):
    return columns(filters), join(filters)

def get_box_data(box_name, mr_dict, column_name):
    return mr_dict.get(box_name, {}).get(column_name, 0.0)

def get_warehouse_data(warehouse_name):
    warehouse_data = box_data.warehouse_qty(warehouse=warehouse_name)
    return {item['box']: item for item in warehouse_data}

def join(filters=None):
    all_box = box_data.all_boxes('Packing Boxes', 'box')
    all_paper = box_data.all_boxes('Packing Paper', 'paper')
    mr_amit = report_utils.get_mapped_data(data=box_data.get_box_order_for_production("Amit Print 'N' Pack, Kishanpura, Baddi"), key='box')
    mr_jai_ambey = report_utils.get_mapped_data(data=box_data.get_box_order_for_production('Jai Ambey Industries'), key='box')
    so_mapping = report_utils.get_mapped_data(data=box_data.get_box_requirement_from_so(), key='box')
    rapl_warehouse_mapping = get_warehouse_data('Packing Boxes - Rapl')
    jai_ambey_warehouse_mapping = get_warehouse_data('Jai Ambey Industries - RAPL')
    amit_warehouse_mapping = get_warehouse_data("Amit Print 'N' Pack - RAPL")
    jai_ambey_supplier = 'Jai Ambey Industries'
    amit_supplier = "Amit Print 'N' Pack, Kishanpura, Baddi"
    rana_supplier = "Rana, Packing Box"

    priority_jai_ambey = report_utils.get_mapped_data(data=box_data.get_paper_supplier_priority(jai_ambey_supplier), key='box')
    priority_amit = report_utils.get_mapped_data(data=box_data.get_paper_supplier_priority(amit_supplier), key='box')
    priority_rana = report_utils.get_mapped_data(data=box_data.get_paper_supplier_priority(rana_supplier), key='box')


    jai_ambey_warehouse_po_box = report_utils.get_mapped_data(data=box_data.get_supplierwise_po(jai_ambey_supplier), key='box')
    amit_warehouse_po_box = report_utils.get_mapped_data(data=box_data.get_supplierwise_po(amit_supplier), key='box')      

    for box in all_box:
        box_name = box.get('box', '-')
        box['production_amit'] = get_box_data(box_name, mr_amit, 'qty')
        box['mr_amit'] = get_box_data(box_name, mr_amit, 'mr_name')
        box['remain_prod_amit'] = box['production_amit'] - get_box_data(box_name, mr_amit, 'received_qty')
        box['mr_jai_ambey'] = get_box_data(box_name, mr_jai_ambey, 'mr_name')
        box['production_jai_ambey'] = get_box_data(box_name, mr_jai_ambey, 'qty')
        box['remain_prod_jai_ambey'] = box['production_jai_ambey'] - get_box_data(box_name, mr_jai_ambey, 'received_qty')

        box['so_qty'] = so_mapping.get(box_name, {'so_qty': 0.0})['so_qty']
        box['so_name'] = so_mapping.get(box_name, {'so_name': ''})['so_name']
        box['priority_jai_ambey'] = priority_jai_ambey.get(box_name, {'priority': 0})['priority']
        box['priority_amit'] = priority_amit.get(box_name, {'priority': 0})['priority']
        box['priority_rana'] = priority_rana.get(box_name, {'priority': 0})['priority']
        
        
        box_particular = box.get('box_particular', '-')
        paper_name = box.get('paper_name', '-')
        if box_particular is None:
            box_particular = ''
        if paper_name is None:
            paper_name = ''

        paper_name = 'PP ' + box_particular + ' ' + paper_name
        
        
        warehouse_item = rapl_warehouse_mapping.get(box_name, {'warehouse_qty': 0.0, 'projected_qty': 0.0})
        box['stock_rapl'] = warehouse_item['warehouse_qty']
        box['projected_rapl'] = warehouse_item['projected_qty']

        jai_warehouse_item = jai_ambey_warehouse_mapping.get(box_name, {'warehouse_qty': 0.0})
        jai_warehouse_paper = jai_ambey_warehouse_mapping.get(paper_name, {'warehouse_qty': 0.0})
        box['stock_jai_ambey'] = jai_warehouse_item['warehouse_qty']
        

        amit_warehouse_item = amit_warehouse_mapping.get(box_name, {'warehouse_qty': 0.0})
        amit_warehouse_paper = amit_warehouse_mapping.get(paper_name, {'warehouse_qty': 0.0})        
        box['stock_amit'] = amit_warehouse_item['warehouse_qty']
        

        # Check if any of the values are None and replace them with an empty string

        for paper in all_paper:
            if paper['paper'] == paper_name:
                box['paper'] = paper_name
                box['jai_paper_stock'] = jai_warehouse_paper['warehouse_qty']
                box['amit_paper_stock'] = amit_warehouse_paper['warehouse_qty']
        box['dispatch_jai_ambey'] = jai_ambey_warehouse_po_box.get(box_name, {'box_qty': 0.0})['box_qty']
        box['po_name_jai_ambey'] = jai_ambey_warehouse_po_box.get(box_name, {'po_name': ''})['po_name']

        box['dispatch_amit'] = amit_warehouse_po_box.get(box_name, {'box_qty': 0.0})['box_qty']
        box['po_name_amit'] = amit_warehouse_po_box.get(box_name, {'po_name': ''})['po_name']

    for box in all_box:
        box['short_qty'] = max(0, (box['so_qty'] + box['msl']) - (box['stock_rapl'] + box['stock_jai_ambey'] + box['stock_amit'] + box['production_amit'] + box['production_jai_ambey']))
        box['dispatch_need_to_complete_so'] = abs(max(0,  box['rapl_msl'] + box['so_qty'] - box['stock_rapl'] - box['dispatch_amit'] -  box['dispatch_jai_ambey']))
        box['total_stock'] = box['stock_amit'] + box['stock_rapl'] + box['stock_jai_ambey']
        box['over_stock_qty'] = min(0, (box['so_qty'] + box['msl']) - (box['stock_rapl'] + box['stock_jai_ambey'] + box['stock_amit'] + box['production_amit'] + box['production_jai_ambey']))
        box['urgent_dispatch'] = box['so_qty'] - box['stock_rapl']
    if filters.get('report_type') == "Box Production":
        all_box.sort(key=lambda x: x['short_qty'], reverse=True)
    if filters.get('report_type') == "Box Dispatch":
        all_box.sort(key=lambda x: x['dispatch_need_to_complete_so'], reverse=True)
    if filters.get('report_type') == "Dead Stock":
        all_box.sort(key=lambda x: x['total_stock'], reverse=True)
        all_box = [item for item in all_box if item['dead_inventory'] > 0 and item['total_stock'] > 0]
    if filters.get('report_type') == "Urgent Dispatch":
        all_box.sort(key=lambda x: x['urgent_dispatch'], reverse=True)
        all_box = [item for item in all_box if item['urgent_dispatch'] > 0]
    return all_box

def priority_cols(builder):
    cols = (builder
        .add_column("J", "Int", 20, "priority_jai_ambey")
        .add_column("A", "Int", 20, "priority_amit")
        .add_column("R", "Int", 20, "priority_rana")
        .build()
    )
    return cols

def links_cols(builder):
    cols = (builder
        .add_column("SOs", "HTML", 100, "so_name") 
        .add_column("MR JAI", "HTML", 100, "mr_jai_ambey")
        .add_column("MR Amit", "HTML", 100, "mr_amit")
        .add_column("POs Amit", "HTML", 100, "po_name_amit") 
        .add_column("POs JAI", "HTML", 100, "po_name_jai_ambey")
        .build()
    )
    return cols

def columns(filters=None):
    cols = None
    if filters.get('report_type') == 'Box Production':
        builder = report_utils.ColumnBuilder()
        cols = (
            builder 
            .add_column("D", "Check", 40, "dead_inventory") 
            .add_column("Box", "Link", 180, "box", options="Item")
            .add_column("Box MSL", "Int", 80, "msl", disable_total=True)
            .add_column("Rapl Stock", "Int", 120, "stock_rapl") 
            .add_column("Amit Stock", "Int", 120, "stock_amit") 
            .add_column("JAI Stock", "Int", 100, "stock_jai_ambey") 
            .add_column("Amit Prod", "Int", 100, "production_amit") 
            .add_column("JAI Prod", "Int", 100, "production_jai_ambey") 
            .add_column("Shortage", "Int", 100, "short_qty")
            .build()
        )

    elif filters.get('report_type') == 'Box Dispatch':
        builder = report_utils.ColumnBuilder()
        cols = (
            builder
            .add_column("D", "Check", 40, "dead_inventory") 
            .add_column("Item", "Link", 180, "box", options="Item")
            .add_column("Rapl MSL", "Int", 100, "rapl_msl")
            .add_column("SO", "Int", 80, "so_qty")
            .add_column("Jai Dispatch", "Int", 120, "dispatch_jai_ambey")
            .add_column("Amit Dispatch", "Int", 120, "dispatch_amit")
            .add_column("Rapl Stock", "Int", 100, "stock_rapl") 
            .add_column("Dispatch Need", "Int", 120, "dispatch_need_to_complete_so")
            .add_column("Amit Stock", "Int", 100, "stock_amit") 
            .add_column("JAI Stock", "Int", 100, "stock_jai_ambey")
            .build()
        )
    elif filters.get('report_type') == 'Dead Stock':
        builder = report_utils.ColumnBuilder()
        cols = (
            builder
            .add_column("D", "Check", 40, "dead_inventory") 
            .add_column("Item", "Link", 180, "box", options="Item")
            .add_column("Rapl Stock", "Int", 100, "stock_rapl") 
            .add_column("Amit Stock", "Int", 100, "stock_amit") 
            .add_column("JAI Stock", "Int", 100, "stock_jai_ambey")
            .add_column("Total Stock", "Int", 100, "total_stock")
            .build()
        )
    elif filters.get('report_type') == 'Urgent Dispatch':
        builder = report_utils.ColumnBuilder()
        cols = (
            builder
            .add_column("D", "Check", 40, "dead_inventory") 
            .add_column("Item", "Link", 180, "box", options="Item")
            .add_column("Rapl Stock", "Int", 100, "stock_rapl") 
            .add_column("SO", "Int", 80, "so_qty")
            .add_column("Urgent Dispatch", "Int", "urgent_dispatch", "urgent_dispatch")
            .build()
        )
    if filters.get('paper_stock'):
        cols = (
            builder
            .add_column("Paper", "Link", 180, "paper", options="Item")
            .add_column("Amit Paper", "Int", 100, "amit_paper_stock", disable_total="True")
            .add_column("Jai_paper_stock", "Int", 100, "jai_paper_stock", disable_total="True")
            .build()
        )
    
    if filters.get('over_stock'):
        cols = (
            builder
            .add_column("Over Stock", "Int", 100, "over_stock_qty")
            .build()
        )
    if filters.get('add_links'):
        cols = links_cols(builder)
    if filters.get('add_priority'):
        cols = priority_cols(builder)
    
    return cols