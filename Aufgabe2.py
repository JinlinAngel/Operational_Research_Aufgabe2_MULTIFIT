# Aufgabe 2

# List Scheduling
def ls(p, m, order=None):
    # wenn nichts übergeben wird, dann normale Reihenfolge
    if order == None:
        order = list(range(len(p)))

    machs = [0]*m
    erg = [[] for _ in range(m)]

    for j in order:
        t = p[j]
        #Maschine mit wenigster Zeit finden
        min_m = min(range(m), key=lambda i: machs[i])
        erg[min_m].append(j)
        machs[min_m] += t

    cmax = max(machs)
    return erg, machs, cmax


# LPT
def lpt(p, m):
    #sortieren nach größter zeit zuerst
    jobs = list(range(len(p)))
    jobs.sort(key=lambda j: p[j], reverse=True)
    return ls(p, m, order=jobs)



def ffd(p, C):
# als Sub-Routine für MULTIFIT

#p: liste der bearbeitungszeiten
#C: kapazität pro bin (kandidaten-makespan)
#rückgabe:
#bins  = liste von bins, jeder bin ist liste von job-indizes
#loads = zugehörige auslastungen
#None = falls C zu klein

    jobs = list(range(len(p)))
    jobs.sort(key=lambda j: p[j], reverse=True)

    bins = []   # jeder eintrag: liste von jobs
    loads = []  # summe der zeiten pro bin

    for j in jobs:
        t = p[j]
        if t > C:
            return None, None
        placed = False

        # versuche job in existierende bins zu packen
        for i in range(len(bins)):
            if loads[i] + t <= C:
                bins[i].append(j)
                loads[i] += t
                placed = True
                break

        # wenn kein bin gepasst hat -> neuen bin aufmachen
        if not placed:
            bins.append([j])
            loads.append(t)

    return bins, loads


def multifit(p, m):

#MULTIFIT-algorithmus für P||C_max.
#p: liste der bearbeitungszeiten
#m: anzahl der maschinen

#Rückgabe: (erg, machs, cmax)
#erg   = zuordnung: erg[i] = liste von jobs auf maschine i
#machs = gesamtzeit pro Maschine
#cmax  = maximale Maschinenlaufzeit

    n = len(p)
    if n == 0 or m <= 0:
        return [[] for _ in range(m)], [0]*m, 0

    # untere schranke: max( max_j p_j, ceil(sum p_j / m) )
    s = sum(p)
    pmax = max(p)
    lb = max(pmax, (s + m - 1) // m)


    # obere schranke: cmax von LPT
    erg_lpt, machs_lpt, cmax_lpt = lpt(p, m)
    ub = cmax_lpt

    # Falls Schranken schon zusammenfallen: LPT-Lösung reicht
    if lb >= ub:
        return erg_lpt, machs_lpt, ub

    best_bins = None
    best_loads = None

    # binärsuche auf C
    while lb < ub:
        C = (lb + ub) // 2

        bins, loads = ffd(p, C)
        if bins is None:
            #Falls in FFD festgestellt wird, dass ein Job > C ist
            lb = C + 1
            continue
        
        if len(bins) > m:
            #Brauchen mehr als m bins → C zu klein
            lb = C + 1
        else:
            #Passt in höchstens m bins → C machbar, nach unten gehen
            ub = C
            best_bins = [b[:] for b in bins] #direkt kopieren, weniger Nebeneffekte
            best_loads = loads[:] 

    #falls nix gesichert wurde (sollte nicht passieren) -> fallback LPT
    if best_bins is None:
        return erg_lpt, machs_lpt, cmax_lpt

    #wenn weniger bins als Maschinen: leere Maschinen anhängen
    while len(best_bins) < m:
        best_bins.append([])
        best_loads.append(0)

    cmax = max(best_loads) if best_loads else 0
    return best_bins, best_loads, cmax


#ausgabe
def printplan(name, erg, machs, cmax, p):
    print("=== "+name+" ===")
    for i in range(len(erg)):
        print("maschine",i,": ", end="")
        for j in erg[i]:
            print("job",j,"(p="+str(p[j])+") ",end="")
        print("| summe:",machs[i])
    print("cmax =",cmax,"\n")


#Laufzeit und Speicher messen
#Test Funktion

def test(algo, p, m):
    tracemalloc.start()
    t1 = time.time()
    erg, machs, cmax = algo(p,m)
    t2 = time.time()
    curr,peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return t2-t1, peak, erg, machs, cmax


# z.B
def main():
    m = 3
    p = [2,14,4,16,6,5,3]


    t_mf, mem_mf, erg_mf, machs_mf, c_mf = test(multifit, p, m)

    printplan("multifit", erg_mf, machs_mf, c_mf, p)
    print("zeit:", round(t_mf,6), "s mem:", round(mem_mf/1024,1), "kb")






# Aufgabe 3
import yaml
import random
import time
import tracemalloc
from pathlib import Path
import matplotlib.pyplot as plt


# testinstanzen laden
def load_instances_from_zip():
    # Alle YAML-Instanzen aus dem Ordner 'instances' laden
    inst_dir = Path("instances")
    if not inst_dir.exists():
        print("FEHLER: konnte Ordner 'instances' nicht finden")
        return []

    instances = []

    # Alle .yaml/.yml Dateien im Ordner aufsammeln
    try:
        files = [p for p in inst_dir.iterdir() if p.is_file() and p.suffix.lower() in (".yaml", ".yml")]
    except Exception as e:
        print("WARNUNG: konnte Ordner 'instances' nicht auflisten:", e)
        return []

    for fpath in files:
        try:
            txt = fpath.read_text(encoding="utf-8")
        except Exception as e:
            print(f"WARNUNG: konnte {fpath} nicht lesen:", e)
            continue
        try:
            docs = list(yaml.safe_load_all(txt))
        except Exception as e:
            print(f"WARNUNG: YAML-Parsing-Fehler in {fpath}:", e)
            continue

        # jede Instanz speichern
        for inst in docs:
            if isinstance(inst, dict):
                inst["__file"] = fpath.name
                instances.append(inst)

    print("geladen:", len(instances), "instanzen aus ordner 'instances'")
    return instances


# multifit messen
def measure_multifit(p, m):
    # Laufzeit und Speicher messen
    tracemalloc.start()
    t1 = time.time()
    erg, machs, cmax = multifit(p, m)
    t2 = time.time()
    curr, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "cmax": cmax,
        "runtime": t2 - t1,
        "peak_kb": peak / 1024,
    }


"""

Die zusätzlichen Instanzen wurden im Code zufällig erzeugt.
Für vary_n bleibt m = 10 fest und n wird schrittweise erhöht
(50, 100, 200, 400, 800). Für vary_m bleibt n = 200 fest und
es werden verschiedene maschinenzahlen getestet (2, 5, 10, 20, 40).
Die Bearbeitungszeiten der Jobs wurden dabei zufällig von 5 bis 100 gewählt.

"""

# erzeugt künstliche Instanzen wo n variiert
def generate_vary_n():
    # m konstant = 10
    # n wächst
    ns = [50, 100, 200, 400, 800]
    r = random.Random(42)

    out = []
    for i, n in enumerate(ns):
        jobs = [r.randint(5, 100) for _ in range(n)]
        out.append({
            "id": f"vn_{i}",
            "num_machines": 10,
            "jobs": jobs,
            "__set": "vary_n"
        })
    return out


# erzeugt künstliche Instanzen wo m variiert
def generate_vary_m():
    # n konstant = 200
    r = random.Random(1337)
    jobs = [r.randint(5, 100) for _ in range(200)]
    ms = [2, 5, 10, 20, 40]

    out = []
    for i, m in enumerate(ms):
        out.append({
            "id": f"vm_{i}",
            "num_machines": m,
            "jobs": jobs,
            "__set": "vary_m"
        })
    return out


# plot hilfsfunktion
def plot_line(xs, ys, xlabel, ylabel, titel, outpath):
    plt.figure()
    plt.plot(xs, ys, "o-")
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(titel)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(outpath)
    plt.close()


# aufgabe 3 start
def run_aufgabe3():

    out_dir = Path("out_multifit")
    out_dir.mkdir(exist_ok=True)

    alle = []

    # 1. testinstanzen laden
    print("\n### teste multifit auf bereitgestellten instanzen ###")
    provided = load_instances_from_zip()

    for inst in provided:
        p = list(map(int, inst["jobs"]))
        m = int(inst["num_machines"])
        res = measure_multifit(p, m)

        print(inst["__file"], "id=", inst.get("id"),
              "m=", m, "n=", len(p),
              "Cmax=", res["cmax"],
              "zeit=", round(res["runtime"], 4),
              "s mem=", round(res["peak_kb"], 1), "KB")

        alle.append({
            "set": inst["__file"],
            "id": inst.get("id"),
            "m": m,
            "n": len(p),
            **res
        })

    # 2. künstliche Instanzen: n variieren
    print("\n### n variieren (m = 10) ###")
    vn = generate_vary_n()
    for inst in vn:
        p = inst["jobs"]
        m = inst["num_machines"]
        res = measure_multifit(p, m)

        print("vary_n:", inst["id"], "n=", len(p), "m=", m,
              "Cmax=", res["cmax"],
              "zeit=", round(res["runtime"], 4),
              "s mem=", round(res["peak_kb"], 1), "KB")

        alle.append({
            "set": "vary_n",
            "id": inst["id"],
            "m": m,
            "n": len(p),
            **res
        })

    # 3. künstliche Instanzen: m variieren
    print("\n### m variieren (n = 200) ###")
    vm = generate_vary_m()
    for inst in vm:
        p = inst["jobs"]
        m = inst["num_machines"]
        res = measure_multifit(p, m)

        print("vary_m:", inst["id"], "n=", len(p), "m=", m,
              "Cmax=", res["cmax"],
              "zeit=", round(res["runtime"], 4),
              "s mem=", round(res["peak_kb"], 1), "KB")

        alle.append({
            "set": "vary_m",
            "id": inst["id"],
            "m": m,
            "n": len(p),
            **res
        })

    #4. csv speichern
    import csv
    csv_path = out_dir / "multifit_results.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(alle[0].keys()))
        w.writeheader()
        w.writerows(alle)

    print("\ncsv gespeichert in:", csv_path)

    # 5. diagramme bauen
    # n variation
    vn2 = [r for r in alle if r["set"] == "vary_n"]
    if vn2:
        vn2 = sorted(vn2, key=lambda r: r["n"])
        xs = [r["n"] for r in vn2]
        plot_line(xs, [r["runtime"] for r in vn2],
                  "n", "zeit (s)", "laufzeit vs n (random_instance)",
                  out_dir / "random_instance_runtime_vs_n.png")
        plot_line(xs, [r["peak_kb"] for r in vn2],
                  "n", "peak mem (KB)", "speicher vs n (random_instance)",
                  out_dir / "random_instance_memory_vs_n.png")

    # m variation
    vm2 = [r for r in alle if r["set"] == "vary_m"]
    if vm2:
        vm2 = sorted(vm2, key=lambda r: r["m"])
        xs = [r["m"] for r in vm2]
        # Zufallsserien ("random_instance_")
        plot_line(xs, [r["runtime"] for r in vm2],
                  "m", "zeit (s)", "laufzeit vs m (random_instance)",
                  out_dir / "random_instance_runtime_vs_m.png")
        plot_line(xs, [r["peak_kb"] for r in vm2],
                  "m", "peak mem (KB)", "speicher vs m (random_instance)",
                  out_dir / "random_instance_memory_vs_m.png")


    # 5e. Einzelkurven für jeweils eine Instanz pro Set (small/medium)
    #     -> entspricht stilistisch den random/vary_* Kurven

    M_GRID_DEFAULT = [2, 5, 10, 20, 40]

    def derive_n_grid(n_max):
        # dynamisches n-Gitter aus Anteilen der vollen Länge
        # immer aufsteigend, eindeutig, mindestens 1 und höchstens n_max
        ratios = [0.1, 0.2, 0.4, 0.6, 0.8, 1.0]
        raw = {max(1, min(n_max, round(n_max * r))) for r in ratios}
        raw.add(n_max)
        return sorted(raw)

    def plot_single_vs_m_for_instance(p_full, set_name, inst_id, m_grid=None):
        if not m_grid:
            m_grid = M_GRID_DEFAULT
        xs = []
        ys_rt = []
        ys_mem = []
        for m in m_grid:
            res = measure_multifit(p_full, m)
            xs.append(m)
            ys_rt.append(res["runtime"])
            ys_mem.append(res["peak_kb"])
        safe = Path(set_name).stem
        plot_line(xs, ys_rt, "m", "zeit (s)", f"laufzeit vs m – {safe} (id={inst_id})", out_dir / f"runtime_vs_m_{safe}_id{inst_id}.png")
        plot_line(xs, ys_mem, "m", "peak mem (KB)", f"speicher vs m – {safe} (id={inst_id})", out_dir / f"memory_vs_m_{safe}_id{inst_id}.png")

    def plot_single_vs_n_for_instance(p_full, base_m, set_name, inst_id):
        n_grid = derive_n_grid(len(p_full))
        xs = []
        ys_rt = []
        ys_mem = []
        for n in n_grid:
            p = list(map(int, p_full[:n]))  # deterministisch: Präfix der Jobs
            res = measure_multifit(p, base_m)
            xs.append(n)
            ys_rt.append(res["runtime"])
            ys_mem.append(res["peak_kb"])
        safe = Path(set_name).stem
        plot_line(xs, ys_rt, "n", "zeit (s)", f"laufzeit vs n – {safe} (id={inst_id}, m={base_m})", out_dir / f"runtime_vs_n_{safe}_id{inst_id}.png")
        plot_line(xs, ys_mem, "n", "peak mem (KB)", f"speicher vs n – {safe} (id={inst_id}, m={base_m})", out_dir / f"memory_vs_n_{safe}_id{inst_id}.png")

    # Für alle Sets im Ordner 'instances': immer eine Instanz wählen (id=0 wenn vorhanden)
    provided_sets = sorted({inst.get("__file") for inst in provided})
    for set_name in provided_sets:
        items = [inst for inst in provided if inst.get("__file") == set_name]
        if not items:
            continue
        # Bevorzugt id=0; sonst erste Instanz
        target = next((x for x in items if x.get("id") == 0), items[0])
        inst_id = target.get("id", "?")
        p_full = list(map(int, target["jobs"]))
        base_m = int(target["num_machines"])  # für vs_n verwenden wir m der Datei

        # vs m (Jobs unverändert, m variieren)
        plot_single_vs_m_for_instance(p_full, set_name, inst_id)

        # vs n (m fix = base_m, n über Präfixe variieren)
        plot_single_vs_n_for_instance(p_full, base_m, set_name, inst_id)

    print("\nAUFGABE 3 abgeschlossen.")
    print("ergebnisse + plots in:", out_dir)

if __name__=="__main__":
    main()          # bisheriges Beispiel
    run_aufgabe3()  # aufg 3 laufen lassen
