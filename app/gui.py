
import logging
import sys
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from typing import Optional, List, Tuple


# --- Logging setup ---
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler("gui.log", encoding="utf-8"),
        logging.StreamHandler(sys.stderr),
    ]
)
logger = logging.getLogger("pms.gui")

logger.info("Starting GUI module import...")

from .db import Base, engine
from . import models as m
from .repository import (
    get_session,
    list_cities, create_city, update_city, delete_city,
    list_neighborhoods, create_neighborhood, update_neighborhood, delete_neighborhood,
    list_streets, create_street, update_street, delete_street,
    list_police_stations, create_police_station, update_police_station, delete_police_station,
)


# Ensure tables exist
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured.")
except Exception as e:
    logger.exception("Failed to create tables.")
    raise

# Helpers to format display strings

def city_label(city: m.City) -> str:
    parts = [city.name]
    if city.state:
        parts.append(city.state)
    if city.country:
        parts.append(city.country)
    return ", ".join(parts)


def neighborhood_label(nb: m.Neighborhood, city_map: dict[int, m.City]) -> str:
    city = city_map.get(nb.city_id)
    return f"{nb.name} ({city_label(city) if city else 'Unknown City'})"


class CrudDialog(tk.Toplevel):
    def __init__(self, parent: tk.Widget, title: str):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.result = None
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.bind("<Escape>", lambda e: self.on_cancel())
        self.grab_set()

    def on_ok(self):
        self.result = True
        self.destroy()

    def on_cancel(self):
        self.result = False
        self.destroy()


class CityDialog(CrudDialog):
    def __init__(self, parent, title: str, city: Optional[m.City] = None):
        super().__init__(parent, title)
        frm = ttk.Frame(self, padding=10)
        frm.grid(sticky="nsew")
        ttk.Label(frm, text="Name").grid(row=0, column=0, sticky="w")
        self.name_var = tk.StringVar(value=(city.name if city else ""))
        ttk.Entry(frm, textvariable=self.name_var, width=30).grid(row=0, column=1, sticky="w")

        ttk.Label(frm, text="State").grid(row=1, column=0, sticky="w")
        self.state_var = tk.StringVar(value=(city.state if city else ""))
        ttk.Entry(frm, textvariable=self.state_var, width=10).grid(row=1, column=1, sticky="w")

        ttk.Label(frm, text="Country").grid(row=2, column=0, sticky="w")
        self.country_var = tk.StringVar(value=(city.country if city else ""))
        ttk.Entry(frm, textvariable=self.country_var, width=10).grid(row=2, column=1, sticky="w")

        btns = ttk.Frame(frm)
        btns.grid(row=3, column=0, columnspan=2, pady=(10, 0))
        ttk.Button(btns, text="Cancel", command=self.on_cancel).grid(row=0, column=0, padx=5)
        ttk.Button(btns, text="Save", command=self.validate).grid(row=0, column=1, padx=5)

    def validate(self):
        if not self.name_var.get().strip():
            messagebox.showerror("Validation", "Name is required")
            return
        self.on_ok()


class NeighborhoodDialog(CrudDialog):
    def __init__(self, parent, title: str, cities: List[m.City], nb: Optional[m.Neighborhood] = None):
        super().__init__(parent, title)
        self.cities = cities
        frm = ttk.Frame(self, padding=10)
        frm.grid(sticky="nsew")

        ttk.Label(frm, text="Name").grid(row=0, column=0, sticky="w")
        self.name_var = tk.StringVar(value=(nb.name if nb else ""))
        ttk.Entry(frm, textvariable=self.name_var, width=30).grid(row=0, column=1, sticky="w")

        ttk.Label(frm, text="City").grid(row=1, column=0, sticky="w")
        self.city_var = tk.StringVar()
        self.city_combo = ttk.Combobox(frm, textvariable=self.city_var, state="readonly", width=28)
        options = [city_label(c) for c in self.cities]
        self.city_combo["values"] = options
        self.city_combo.grid(row=1, column=1, sticky="w")
        if nb:
            # Preselect
            try:
                idx = [c.id for c in self.cities].index(nb.city_id)
                self.city_combo.current(idx)
            except ValueError:
                pass

        btns = ttk.Frame(frm)
        btns.grid(row=2, column=0, columnspan=2, pady=(10, 0))
        ttk.Button(btns, text="Cancel", command=self.on_cancel).grid(row=0, column=0, padx=5)
        ttk.Button(btns, text="Save", command=self.validate).grid(row=0, column=1, padx=5)

    def selected_city_id(self) -> Optional[int]:
        # Use cached value if set, else get from combobox
        if hasattr(self, '_selected_city_id'):
            return self._selected_city_id
        idx = self.city_combo.current()
        return self.cities[idx].id if idx >= 0 else None

    def validate(self):
        if not self.name_var.get().strip():
            messagebox.showerror("Validation", "Name is required")
            return
        idx = self.city_combo.current()
        if idx < 0:
            messagebox.showerror("Validation", "City is required")
            return
        # Save the selected city id before dialog is destroyed
        self._selected_city_id = self.cities[idx].id
        self.on_ok()


class StreetDialog(CrudDialog):
    def __init__(self, parent, title: str, neighborhoods: List[m.Neighborhood], nb_labels: List[str], st: Optional[m.Street] = None):
        super().__init__(parent, title)
        self.neighborhoods = neighborhoods
        self.nb_labels = nb_labels
        frm = ttk.Frame(self, padding=10)
        frm.grid(sticky="nsew")

        ttk.Label(frm, text="Name").grid(row=0, column=0, sticky="w")
        self.name_var = tk.StringVar(value=(st.name if st else ""))
        ttk.Entry(frm, textvariable=self.name_var, width=40).grid(row=0, column=1, sticky="w")

        ttk.Label(frm, text="Neighborhood").grid(row=1, column=0, sticky="w")
        self.nb_var = tk.StringVar()
        self.nb_combo = ttk.Combobox(frm, textvariable=self.nb_var, state="readonly", width=38)
        self.nb_combo["values"] = nb_labels
        self.nb_combo.grid(row=1, column=1, sticky="w")
        if st:
            try:
                idx = [n.id for n in self.neighborhoods].index(st.neighborhood_id)
                self.nb_combo.current(idx)
            except ValueError:
                pass

        btns = ttk.Frame(frm)
        btns.grid(row=2, column=0, columnspan=2, pady=(10, 0))
        ttk.Button(btns, text="Cancel", command=self.on_cancel).grid(row=0, column=0, padx=5)
        ttk.Button(btns, text="Save", command=self.validate).grid(row=0, column=1, padx=5)

    def selected_neighborhood_id(self) -> Optional[int]:
        # Use cached value if set, else get from combobox
        if hasattr(self, '_selected_neighborhood_id'):
            return self._selected_neighborhood_id
        idx = self.nb_combo.current()
        return self.neighborhoods[idx].id if idx >= 0 else None

    def validate(self):
        if not self.name_var.get().strip():
            messagebox.showerror("Validation", "Name is required")
            return
        idx = self.nb_combo.current()
        if idx < 0:
            messagebox.showerror("Validation", "Neighborhood is required")
            return
        # Save the selected neighborhood id before dialog is destroyed
        self._selected_neighborhood_id = self.neighborhoods[idx].id
        self.on_ok()


class PoliceStationDialog(CrudDialog):
    def __init__(self, parent, title: str, cities: List[m.City], ps: Optional[m.PoliceStation] = None):
        super().__init__(parent, title)
        self.cities = cities
        frm = ttk.Frame(self, padding=10)
        frm.grid(sticky="nsew")

        ttk.Label(frm, text="Name").grid(row=0, column=0, sticky="w")
        self.name_var = tk.StringVar(value=(ps.name if ps else ""))
        ttk.Entry(frm, textvariable=self.name_var, width=40).grid(row=0, column=1, sticky="w")

        ttk.Label(frm, text="City (optional)").grid(row=1, column=0, sticky="w")
        self.city_var = tk.StringVar()
        self.city_combo = ttk.Combobox(frm, textvariable=self.city_var, state="readonly", width=38)
        city_options = ["<None>"] + [city_label(c) for c in self.cities]
        self.city_combo["values"] = city_options
        self.city_combo.grid(row=1, column=1, sticky="w")
        # Preselect
        if ps and ps.city_id is not None:
            try:
                idx = [c.id for c in self.cities].index(ps.city_id)
                self.city_combo.current(idx + 1)
            except ValueError:
                self.city_combo.current(0)
        else:
            self.city_combo.current(0)

        ttk.Label(frm, text="Address (optional)").grid(row=2, column=0, sticky="w")
        self.address_var = tk.StringVar(value=(ps.address if ps and ps.address else ""))
        ttk.Entry(frm, textvariable=self.address_var, width=40).grid(row=2, column=1, sticky="w")

        btns = ttk.Frame(frm)
        btns.grid(row=3, column=0, columnspan=2, pady=(10, 0))
        ttk.Button(btns, text="Cancel", command=self.on_cancel).grid(row=0, column=0, padx=5)
        ttk.Button(btns, text="Save", command=self.validate).grid(row=0, column=1, padx=5)


    def selected_city_id(self) -> Optional[int]:
        # Use cached value if set, else get from combobox
        if hasattr(self, '_selected_city_id'):
            return self._selected_city_id
        idx = self.city_combo.current()
        if idx <= 0:
            return None
        return self.cities[idx - 1].id

    def validate(self):
        if not self.name_var.get().strip():
            messagebox.showerror("Validation", "Name is required")
            return
        idx = self.city_combo.current()
        # Save the selected city id before dialog is destroyed
        if idx > 0:
            self._selected_city_id = self.cities[idx - 1].id
        else:
            self._selected_city_id = None
        self.on_ok()


class BaseTab(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="both", expand=True)

    def show_error(self, err: Exception):
        messagebox.showerror("Error", str(err))


class CitiesTab(BaseTab):
    def __init__(self, master):
        super().__init__(master)
        # Controls
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=5)
        ttk.Button(toolbar, text="Add", command=self.add_city).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Edit", command=self.edit_city).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Delete", command=self.delete_city).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Refresh", command=self.refresh).pack(side="left", padx=2)

        # Tree
        cols = ("id", "name", "state", "country")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c.capitalize())
        self.tree.column("id", width=60, anchor="center")
        self.tree.pack(fill="both", expand=True)

        self.refresh()

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        with get_session() as s:
            for c in list_cities(s):
                self.tree.insert("", "end", iid=str(c.id), values=(c.id, c.name, c.state or "", c.country or ""))

    def get_selected_id(self) -> Optional[int]:
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def add_city(self):
        dlg = CityDialog(self, "Add City")
        self.wait_window(dlg)
        if dlg.result:
            try:
                with get_session() as s:
                    create_city(s, dlg.name_var.get(), dlg.state_var.get(), dlg.country_var.get())
                self.refresh()
            except Exception as e:
                self.show_error(e)

    def edit_city(self):
        cid = self.get_selected_id()
        if not cid:
            return
        with get_session() as s:
            city = s.get(m.City, cid)
        dlg = CityDialog(self, "Edit City", city)
        self.wait_window(dlg)
        if dlg.result:
            try:
                with get_session() as s:
                    update_city(s, cid, dlg.name_var.get(), dlg.state_var.get(), dlg.country_var.get())
                self.refresh()
            except Exception as e:
                self.show_error(e)

    def delete_city(self):
        cid = self.get_selected_id()
        if not cid:
            return
        if not messagebox.askyesno("Confirm", "Delete selected city and related neighborhoods/streets/stations?"):
            return
        try:
            with get_session() as s:
                delete_city(s, cid)
            self.refresh()
        except Exception as e:
            self.show_error(e)


class NeighborhoodsTab(BaseTab):
    def __init__(self, master):
        super().__init__(master)
        # Filters and toolbar
        top = ttk.Frame(self)
        top.pack(fill="x", pady=5)
        ttk.Label(top, text="City:").pack(side="left")
        self.city_filter_var = tk.StringVar()
        self.city_filter_combo = ttk.Combobox(top, textvariable=self.city_filter_var, state="readonly", width=30)
        self.city_filter_combo.pack(side="left", padx=5)
        self.city_filter_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        ttk.Button(top, text="Add", command=self.add_nb).pack(side="left", padx=2)
        ttk.Button(top, text="Edit", command=self.edit_nb).pack(side="left", padx=2)
        ttk.Button(top, text="Delete", command=self.delete_nb).pack(side="left", padx=2)
        ttk.Button(top, text="Refresh", command=self.refresh).pack(side="left", padx=2)

        cols = ("id", "name", "city")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c.capitalize())
        self.tree.column("id", width=60, anchor="center")
        self.tree.pack(fill="both", expand=True)

        self.cities_cache: List[m.City] = []
        self.refresh_filters()
        self.refresh()

    def refresh_filters(self):
        with get_session() as s:
            self.cities_cache = list_cities(s)
        options = ["<All>"] + [city_label(c) for c in self.cities_cache]
        self.city_filter_combo["values"] = options
        if not self.city_filter_combo.current():
            self.city_filter_combo.current(0)

    def selected_city_filter_id(self) -> Optional[int]:
        idx = self.city_filter_combo.current()
        if idx <= 0:
            return None
        return self.cities_cache[idx - 1].id

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        city_id = self.selected_city_filter_id()
        with get_session() as s:
            nbs = list_neighborhoods(s, city_id=city_id)
            city_map = {c.id: c for c in list_cities(s)}
            for nb in nbs:
                self.tree.insert("", "end", iid=str(nb.id), values=(nb.id, nb.name, city_label(city_map.get(nb.city_id))))

    def get_selected_id(self) -> Optional[int]:
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def add_nb(self):
        self.refresh_filters()
        dlg = NeighborhoodDialog(self, "Add Neighborhood", self.cities_cache)
        self.wait_window(dlg)
        if dlg.result:
            try:
                with get_session() as s:
                    create_neighborhood(s, dlg.name_var.get(), dlg.selected_city_id())
                self.refresh()
            except Exception as e:
                self.show_error(e)

    def edit_nb(self):
        nb_id = self.get_selected_id()
        if not nb_id:
            return
        with get_session() as s:
            nb = s.get(m.Neighborhood, nb_id)
            cities = list_cities(s)
        dlg = NeighborhoodDialog(self, "Edit Neighborhood", cities, nb)
        self.wait_window(dlg)
        if dlg.result:
            try:
                with get_session() as s:
                    update_neighborhood(s, nb_id, dlg.name_var.get(), dlg.selected_city_id())
                self.refresh()
            except Exception as e:
                self.show_error(e)

    def delete_nb(self):
        nb_id = self.get_selected_id()
        if not nb_id:
            return
        if not messagebox.askyesno("Confirm", "Delete selected neighborhood and related streets?"):
            return
        try:
            with get_session() as s:
                delete_neighborhood(s, nb_id)
            self.refresh()
        except Exception as e:
            self.show_error(e)


class StreetsTab(BaseTab):
    def __init__(self, master):
        super().__init__(master)
        top = ttk.Frame(self)
        top.pack(fill="x", pady=5)

        ttk.Button(top, text="Add", command=self.add_street).pack(side="left", padx=2)
        ttk.Button(top, text="Edit", command=self.edit_street).pack(side="left", padx=2)
        ttk.Button(top, text="Delete", command=self.delete_street).pack(side="left", padx=2)
        ttk.Button(top, text="Refresh", command=self.refresh).pack(side="left", padx=2)

        cols = ("id", "name", "neighborhood", "city")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c.capitalize())
        self.tree.column("id", width=60, anchor="center")
        self.tree.pack(fill="both", expand=True)

        self.refresh()

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        with get_session() as s:
            nbs = list_neighborhoods(s)
            nb_map = {nb.id: nb for nb in nbs}
            city_ids = {nb.city_id for nb in nbs}
            cities = [c for c in list_cities(s) if c.id in city_ids]
            city_map = {c.id: c for c in cities}
            for st in list_streets(s):
                nb = nb_map.get(st.neighborhood_id)
                city = city_map.get(nb.city_id) if nb else None
                self.tree.insert(
                    "",
                    "end",
                    iid=str(st.id),
                    values=(st.id, st.name, nb.name if nb else "", city_label(city) if city else ""),
                )

    def get_selected_id(self) -> Optional[int]:
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def _load_nb_choices(self) -> Tuple[List[m.Neighborhood], List[str]]:
        with get_session() as s:
            nbs = list_neighborhoods(s)
            cities = list_cities(s)
        city_map = {c.id: c for c in cities}
        labels = [neighborhood_label(nb, city_map) for nb in nbs]
        return nbs, labels

    def add_street(self):
        nbs, labels = self._load_nb_choices()
        dlg = StreetDialog(self, "Add Street", nbs, labels)
        self.wait_window(dlg)
        if dlg.result:
            try:
                with get_session() as s:
                    create_street(s, dlg.name_var.get(), dlg.selected_neighborhood_id())
                self.refresh()
            except Exception as e:
                self.show_error(e)

    def edit_street(self):
        st_id = self.get_selected_id()
        if not st_id:
            return
        with get_session() as s:
            st = s.get(m.Street, st_id)
        nbs, labels = self._load_nb_choices()
        dlg = StreetDialog(self, "Edit Street", nbs, labels, st)
        self.wait_window(dlg)
        if dlg.result:
            try:
                with get_session() as s:
                    update_street(s, st_id, dlg.name_var.get(), dlg.selected_neighborhood_id())
                self.refresh()
            except Exception as e:
                self.show_error(e)

    def delete_street(self):
        st_id = self.get_selected_id()
        if not st_id:
            return
        if not messagebox.askyesno("Confirm", "Delete selected street?"):
            return
        try:
            with get_session() as s:
                delete_street(s, st_id)
            self.refresh()
        except Exception as e:
            self.show_error(e)


class PoliceStationsTab(BaseTab):
    def __init__(self, master):
        super().__init__(master)
        top = ttk.Frame(self)
        top.pack(fill="x", pady=5)
        ttk.Label(top, text="City:").pack(side="left")
        self.city_filter_var = tk.StringVar()
        self.city_filter_combo = ttk.Combobox(top, textvariable=self.city_filter_var, state="readonly", width=30)
        self.city_filter_combo.pack(side="left", padx=5)
        self.city_filter_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        ttk.Button(top, text="Add", command=self.add_ps).pack(side="left", padx=2)
        ttk.Button(top, text="Edit", command=self.edit_ps).pack(side="left", padx=2)
        ttk.Button(top, text="Delete", command=self.delete_ps).pack(side="left", padx=2)
        ttk.Button(top, text="Refresh", command=self.refresh).pack(side="left", padx=2)

        cols = ("id", "name", "city", "address")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c.capitalize())
        self.tree.column("id", width=60, anchor="center")
        self.tree.pack(fill="both", expand=True)

        self.cities_cache: List[m.City] = []
        self.refresh_filters()
        self.refresh()

    def refresh_filters(self):
        with get_session() as s:
            self.cities_cache = list_cities(s)
        options = ["<All>"] + [city_label(c) for c in self.cities_cache]
        self.city_filter_combo["values"] = options
        if not self.city_filter_combo.current():
            self.city_filter_combo.current(0)

    def selected_city_filter_id(self) -> Optional[int]:
        idx = self.city_filter_combo.current()
        if idx <= 0:
            return None
        return self.cities_cache[idx - 1].id

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        city_id = self.selected_city_filter_id()
        with get_session() as s:
            pss = list_police_stations(s, city_id=city_id)
            city_map = {c.id: c for c in list_cities(s)}
            for ps in pss:
                city = city_map.get(ps.city_id) if ps.city_id else None
                self.tree.insert(
                    "",
                    "end",
                    iid=str(ps.id),
                    values=(ps.id, ps.name, city_label(city) if city else "", ps.address or ""),
                )

    def get_selected_id(self) -> Optional[int]:
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def add_ps(self):
        self.refresh_filters()
        dlg = PoliceStationDialog(self, "Add Police Station", self.cities_cache)
        self.wait_window(dlg)
        if dlg.result:
            try:
                with get_session() as s:
                    create_police_station(s, dlg.name_var.get(), dlg.selected_city_id(), dlg.address_var.get())
                self.refresh()
            except Exception as e:
                self.show_error(e)

    def edit_ps(self):
        ps_id = self.get_selected_id()
        if not ps_id:
            return
        with get_session() as s:
            ps = s.get(m.PoliceStation, ps_id)
            cities = list_cities(s)
        dlg = PoliceStationDialog(self, "Edit Police Station", cities, ps)
        self.wait_window(dlg)
        if dlg.result:
            try:
                with get_session() as s:
                    update_police_station(s, ps_id, dlg.name_var.get(), dlg.selected_city_id(), dlg.address_var.get())
                self.refresh()
            except Exception as e:
                self.show_error(e)

    def delete_ps(self):
        ps_id = self.get_selected_id()
        if not ps_id:
            return
        if not messagebox.askyesno("Confirm", "Delete selected police station?"):
            return
        try:
            with get_session() as s:
                delete_police_station(s, ps_id)
            self.refresh()
        except Exception as e:
            self.show_error(e)



class App(tk.Tk):
    def __init__(self):
        logger.info("Initializing main window...")
        super().__init__()
        self.title("Police Management System - Locations")
        self.geometry("800x500")
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        nb.add(CitiesTab(nb), text="Cities")
        nb.add(NeighborhoodsTab(nb), text="Neighborhoods")
        nb.add(StreetsTab(nb), text="Streets")
        nb.add(PoliceStationsTab(nb), text="Police Stations")
        logger.info("Main window initialized.")



def main():
    logger.info("Starting main()...")
    try:
        app = App()
        logger.info("Entering mainloop...")
        app.mainloop()
        logger.info("Exited mainloop.")
    except Exception as e:
        logger.exception("Exception in mainloop:")
        raise



if __name__ == "__main__":
    logger.info("__main__ entrypoint reached.")
    main()
