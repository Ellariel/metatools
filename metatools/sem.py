import graphviz.dot
import numpy as np
import tempfile
import shutil
import semopy
import os
import networkx as nx
import graphviz


from .format import format_p

# it uses graphviz. for windows, use https://graphviz.gitlab.io/download/
# https://arxiv.org/pdf/2106.01140.pdf
# formula = f"""
# ПП =~ {' + '.join(p)}
# НЭ =~ {' + '.join(e)}
# ПП ~ НЭ + {' + '.join(x)} + Группа
# """


def sem(
    data,
    formula,
    method="MLW",  # MLW ULS GLS FIML DWLS WLS
    solver="SLSQP",
    bootstrap=100,
    se_robust=True,
    standardized=True,
    seed=13,
):
    np.random.seed(seed)
    model = semopy.Model(formula)
    model.fit(data, obj=method, solver=solver)
    if bootstrap:
        semopy.bias_correction(model, n=bootstrap, resample_mean=True)
    metrics = (
        semopy.calc_stats(model).T.rename(columns={"Value": "value"})
    )
    stats = model.inspect(std_est=standardized, se_robust=se_robust)
    stats.columns = [i.lower().replace(". ", "_") for i in stats.columns]
    stats = stats.replace("-", np.nan).infer_objects(copy=False)
    return stats, metrics


def sem_report(stats, metrics, decimal=3, format_pval=True):
    if format_pval:
        stats["p-value"] = stats["p-value"].fillna("").apply(
            lambda x: format_p(x, use_letter=False, keep_spaces=False, no_equals=True)
        )
    #metrics = metrics.round(decimal)
    stats = stats.round(decimal)#.fillna("")
    return stats, metrics


def _semplot(model, save_to_file, plot_covs, std_ests):
    tmp_file = os.path.join(tempfile.gettempdir(), "sem_tmp_fig.png")
    fname, ext = os.path.splitext(tmp_file)
    fig = semopy.semplot(
        model, tmp_file, plot_covs=plot_covs, std_ests=std_ests, show=False
    )
    from graphviz import Source
    g = nx.nx_pydot.read_dot(fname)
    for e in g.edges:
        print(e)
        for k, v in g.edges[e].items():
            if k == 'label' and 'p-val' in v:
                g.edges[e]['label'] = g.edges[e]['label'].replace("p-val", "p")
    #import matplotlib.pyplot as plt
    #nx.draw(g, pos=nx.spring_layout(g))  # use spring layout
    #plt.show()
    '''
    if return_fig or save_to_file:
        fig = _semplot(
            model,
            save_to_file,
            plot_covs,
            standardized,
        )
    if return_fig:
            return stats, metrics, fig
    g_ = nx.nx_pydot.to_pydot(g)
    #print(g_)
    fig = Source(str(g_))
    
    '''
    if isinstance(save_to_file, str):
        _, ext = os.path.splitext(save_to_file)
        fig.render(tmp_file, view=False, format=ext[1:], quiet=True)
        shutil.copy(tmp_file + ext, save_to_file)
    return fig