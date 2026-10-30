# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

import logging

from cluster.group import Group
from interpolation.interpolation_data import InterpolationData
from production_unit.production_unit import ProductionUnit
from sites.site import Site

# Offset added to group_id to form virtual site/PU IDs, avoiding collisions with
# real site/PU IDs (which are typically < 10 000).
_GROUP_ID_OFFSET = 100_000


def assign_groups_after_load(regions, simulation_options):
    """HIGH: Merge grouped PUs into virtual single PUs when use_groups is enabled."""
    use_groups = bool(simulation_options.get('use_groups', False))
    if not use_groups:
        return
    for region in regions.values():
        _assign_groups_to_sites(region, simulation_options)


def _assign_groups_to_sites(region, simulation_options):
    """MEDIUM: For each group in region, merge member PUs and add a virtual site."""
    data_interface = region.data_interface
    group_rows = data_interface.groups_for_region(region.id)
    membership_rows = data_interface.group_site_memberships(region.id)
    if not group_rows:
        return

    # Build group objects (data containers only)
    groups_by_id = {}
    for group_row in group_rows:
        group = Group(id_group=group_row['id_group'], region=region)
        groups_by_id[group.id] = group

    # Assign member sites to groups
    site_map = {site.id: site for site in region.sites}
    for membership in membership_rows:
        group_id = membership['id_group']
        site_id = membership['id_site']
        if group_id in groups_by_id and site_id in site_map:
            groups_by_id[group_id].sites.append(site_map[site_id])

    # Merge PUs and build virtual sites
    for group in groups_by_id.values():
        if not group.sites:
            continue

        member_pus = _collect_pus_from_sites(group.sites)
        if not member_pus:
            continue

        merged_pu = _merge_production_units_in_group(group.id, member_pus, simulation_options)
        virtual_site = _create_virtual_site_for_group(group.id, region, group.sites, merged_pu)

        # Add the virtual site to the region
        region.sites.append(virtual_site)

        # Remove original PUs from their sites (they now live in the merged PU)
        for site in group.sites:
            site.group = group  # keep back-reference for diagnostics
            grouped_pu_ids = {pu.id for pu in member_pus}
            site.production_units = [pu for pu in site.production_units if pu.id not in grouped_pu_ids]

        logging.info(
            'Group %s: merged %d PUs from %d sites into virtual site %d.',
            group.id,
            len(member_pus),
            len(group.sites),
            _GROUP_ID_OFFSET + group.id,
        )


def _collect_pus_from_sites(sites):
    """LOW: Flatten all production_units from a list of sites into one list."""
    pus = []
    for site in sites:
        pus.extend(site.production_units)
    return pus


def _merge_production_units_in_group(group_id, member_pus, simulation_options):
    """
    MEDIUM: Build one merged ProductionUnit from all member PUs.

    The merged PU:
    - Gets id = GROUP_ID_OFFSET + group_id
    - Has the union of all sub-production-units from all member PUs
    - Has summed minimum_export requirements across all member PUs
    - Has the union of all available carriers and processes
    - Uses the first member PU's sector and optimization factory
    """
    merged_id = _GROUP_ID_OFFSET + group_id
    first_pu = member_pus[0]

    merged_minimum_export = _sum_minimum_export_data(member_pus)
    merged_carriers = _union_carriers(member_pus)
    merged_process_map = _union_process_maps(member_pus)
    all_sub_pus = _collect_sub_production_units(member_pus)

    # Use a null factory — we manually assign sub-PUs after construction.
    # The constructor calls create_for_start_year(), which would error on the
    # virtual id. _NullSubProductionUnitFactory returns an empty list instead.
    null_factory = _NullSubProductionUnitFactory()

    merged_pu = ProductionUnit(
        id_production_unit=merged_id,
        site=None,  # set by _create_virtual_site_for_group after construction
        sector=first_pu.sector,
        minimum_export_interpolation_data_in_t=merged_minimum_export,
        sub_production_unit_factory=null_factory,
        optimization_factory=first_pu._optimization_factory,
        process_map=merged_process_map,
        carriers=list(merged_carriers),
        simulation_options=simulation_options,
    )

    # Override the empty sub-PU list from the null factory with the real union
    merged_pu.sub_production_units = all_sub_pus
    merged_pu.available_carriers = list(merged_carriers)

    # Update parent references on each transferred sub-PU
    for sub_pu in all_sub_pus:
        sub_pu.id_production_unit = merged_id

    # Recompute start-year pseudo-optimization results now that sub-PUs are set
    merged_pu.optimization_results = merged_pu._extract_pseudo_optimization_results_for_start_year(simulation_options)
    merged_pu._sub_production_unit_inactivity = merged_pu._initialize_sub_production_inactivity()

    return merged_pu


def _sum_minimum_export_data(member_pus):
    """
    LOW: Sum minimum_export_interpolation_data across all member PUs.

    For each product, sums start/end/interim year values independently.
    Products present in only some PUs are included with their original values.
    """
    merged = {}
    for pu in member_pus:
        for product, interp in pu._minimum_export_interpolation_data_in_t.items():
            if product not in merged:
                merged[product] = InterpolationData(
                    value_for_start_year=interp.value_for_start_year,
                    value_for_end_year=interp.value_for_end_year,
                    value_for_interim_year=interp.value_for_interim_year,
                )
            else:
                existing = merged[product]
                interim = _add_optional(existing.value_for_interim_year, interp.value_for_interim_year)
                merged[product] = InterpolationData(
                    value_for_start_year=existing.value_for_start_year + interp.value_for_start_year,
                    value_for_end_year=existing.value_for_end_year + interp.value_for_end_year,
                    value_for_interim_year=interim,
                )
    return merged


def _add_optional(a, b):
    """LOW: Add two values that may be None. None acts as zero."""
    if a is None and b is None:
        return None
    return (a or 0) + (b or 0)


def _union_carriers(member_pus):
    """LOW: Return the set of all carriers across all member PUs."""
    carriers = set()
    for pu in member_pus:
        carriers.update(pu.available_carriers)
    return carriers


def _union_process_maps(member_pus):
    """LOW: Return a merged process_map dict (id_process → process) for all member PUs."""
    merged = {}
    for pu in member_pus:
        for process in pu._original_processes:
            merged[process.id] = process
    return merged


def _collect_sub_production_units(member_pus):
    """LOW: Flatten sub_production_units from all member PUs into one list."""
    sub_pus = []
    for pu in member_pus:
        sub_pus.extend(pu.sub_production_units)
    return sub_pus


def _create_virtual_site_for_group(group_id, region, member_sites, merged_pu):
    """
    MEDIUM: Build a virtual Site that hosts the merged production unit.

    The virtual site's id is GROUP_ID_OFFSET + group_id.
    H2 pipeline context is copied from the first member site.
    """
    virtual_id = _GROUP_ID_OFFSET + group_id
    first_site = member_sites[0]

    virtual_site = Site(
        id_site=virtual_id,
        region=region,
        geometry=first_site.geometry,
        processes=first_site._processes,
    )

    # Wire the merged PU into the virtual site and set its parent reference
    merged_pu._site = virtual_site
    virtual_site.production_units = [merged_pu]

    # Copy H2 pipeline context from the first member site.
    # Set _skip_pipeline_init so that initialize_context() (called later by
    # mesa_simulation) does not overwrite these values with DB lookups for the
    # virtual site id, which has no real pipeline relations.
    virtual_site.pipeline_context = first_site.pipeline_context
    virtual_site._h2_first_accessible_year = first_site._h2_first_accessible_year
    virtual_site._skip_pipeline_init = True

    return virtual_site


class _NullSubProductionUnitFactory:
    """
    LOW: Stub factory that returns an empty sub-PU list.

    Used during merged-PU construction to prevent DB lookups for the virtual id.
    Sub-PUs are assigned manually after construction in _merge_production_units_in_group.
    """

    def create_for_start_year(self, _id_production_unit):
        return []
