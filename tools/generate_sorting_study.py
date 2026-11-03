"""Generate independent synthetic results and optional continuous/discrete figures."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from signal_demo.sorting import (cases, amplitude, signal, phase, signed_circular,
                                 centred_bin, circular_bin_difference, regime, classification, study_report)


def markdown(report):
    rows = ["# Synthetic ten-bin sorting results", "",
            "All signals are independently constructed. These are empirical numerical descriptions of mathematical examples, not clinical observations or image-quality validation.", "",
            "## Protocol", "",
            "Ten centred circular bins use `B(f) = floor(10*(f mod 1)+1/2) mod 10`. The signed difference is phase minus amplitude, wrapped to half a cycle. Antipodal ties retain their unwrapped sign. Each result uses 20,000 uniformly spaced midpoint samples over a complete normalized cycle. All examples have full valid coverage.", "",
            "Continuous pointwise regimes are distance ≤1 BW, >1 to ≤2 BW, and >2 BW, with BW=0.1. The separate user-defined RMSD labels use ≤0.5 BW, >0.5 to ≤1.5 BW, and >1.5 BW. Neither scheme guarantees exact bin agreement. Exact centred-bin mismatch is scored independently.", "",
            "## Complete result table", "",
            "| Synthetic case | Phase | Maximum D | RMSD | RMSD / BW | Different bins | ≤1 BW | 1–2 BW | >2 BW | RMSD label |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |"]
    for row in report['results']:
        fractions = row['pointwise_regime_fractions']
        rows.append(f"| {row['case']} | {row['method']} | {row['maximum_circular_distance']:.6f} | {row['circular_rmsd']:.6f} | {row['classification']['rms_in_bin_widths']:.3f} | {100*row['bin_mismatch_fraction']:.2f}% | {100*fractions[0]:.2f}% | {100*fractions[1]:.2f}% | {100*fractions[2]:.2f}% | {row['classification']['label']} |")
    rows += ["", "## Continuous and discrete figures", "",
             "![Continuous canonical synthetic cases](figures/sorting-continuous.svg)", "",
             "![Discrete ten-bin canonical cases](figures/sorting-discrete.svg)", "",
             "![Continuous constructed limiting families](figures/extremes-continuous.svg)", "",
             "![Discrete constructed limiting families](figures/extremes-discrete.svg)", "",
             "The narrow coloured tracks below each waveform identify centred single/selected-phase and amplitude bins. In the canonical plates, waveform time shading and the RMSD label refer to single phase; both single- and dual-phase curves are plotted in the comparison panels. Each limiting-family row instead uses its explicitly selected phase method. Difference-panel shading is in continuous bin-width units or integer bin units, as labelled. Colours do not encode clinical severity.", "",
             "The four figure plates show the eight canonical and six limiting-family comparisons. The six dashboard-parameter comparisons are included in the complete table and machine-readable report; they are not additional rows in those plates.", "",
             "## Interpretation and limits", "",
             "The linear symmetric example agrees exactly. A linear asymmetric cycle has nonzero single-phase disagreement but exact dual-phase agreement. Half-cosine branches retain within-branch nonlinear disagreement even after dual-phase normalization. A low RMSD label can coexist with nonzero bin mismatch because very close coordinates can straddle a threshold.", "",
             "Constructed extreme examples use epsilon=0.01. Their two phase comparisons can use different waveforms or selected minima; they are not a controlled same-waveform superiority experiment. Reported limiting values apply to the stated constructed families. A numerical example does not prove global sharpness over every possible admissible waveform.", "",
             "Piecewise-linear RMSD is integrated analytically with splits at circular wrap boundaries. Smooth RMSD and duration/bin fractions use midpoint quadrature; maxima use explicit joins and analytic stationary points. A denser-grid sensitivity is checked in tests. Percentages are numerical approximations, with no population or sampling-confidence interpretation.", "",
             "[Formal definitions](SORTING_METHODS.md) · [Machine-readable results](results/sorting-study.json) · [Reproduction](VALIDATION.md).", ""]
    return '\n'.join(rows)


def draw_figures(report, folder):
    import math
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8.0,'axes.titlesize':8.5,
                         'axes.labelsize':8,'xtick.labelsize':7.5,'ytick.labelsize':7.5,
                         'svg.fonttype':'path','axes.spines.top':False,'axes.spines.right':False})
    cyan, magenta, green = '#009dbb', '#b51a86', '#337a57'
    bands = ['#e4f2e8','#fff0d2','#f8e0df']
    labels = {(row['case'],row['method']):row for row in report['results']}
    allcases=cases()
    canonical=[(c, c.methods) for c in allcases[:4]]
    extreme=[(allcases[4],('single',)),(allcases[5],('single',)),(allcases[6],('single',)),
             (allcases[4],('dual',)),(allcases[7],('dual',)),(allcases[8],('dual',))]
    folder.mkdir(parents=True,exist_ok=True)
    for group,entries in [('sorting',canonical),('extremes',extreme)]:
        for discrete in (False,True):
            fig,axes=plt.subplots(len(entries),3,figsize=(7.2,8.5),squeeze=False)
            fig.subplots_adjust(left=.075,right=.985,bottom=.13,top=.86,wspace=.31,hspace=.82)
            kind='discrete' if discrete else 'continuous'
            title=('Canonical synthetic cycles' if group=='sorting' else 'Constructed limiting families')
            fig.suptitle(title+'\n'+('Centred ten-bin analysis' if discrete else 'Continuous circular analysis'),y=.985,fontsize=13,fontweight='bold')
            legend=[Line2D([0],[0],color=cyan,ls='--',label='Single/selected phase'),
                    Line2D([0],[0],color=green,ls=':',label='Dual phase (canonical cases)'),
                    Line2D([0],[0],color=magenta,label='Amplitude')]
            fig.legend(handles=legend,loc='upper center',bbox_to_anchor=(.52,.935),ncol=3,frameon=False,fontsize=7.5)
            for row,(case,methods) in enumerate(entries):
                # Explicit joins avoid losing narrow constructed transitions in the drawing.
                joins=[v[0] for v in case.vertices]+[case.r,case.r*(1-case.pause)]
                x=np.unique(np.r_[np.linspace(0,1,2001),joins])
                a=np.array([amplitude(float(t),case) for t in x])
                s=np.array([signal(float(t),case) for t in x])
                selected=methods[0]
                p=np.array([phase(float(t),case.r,selected) for t in x])
                regime_values=np.array([regime(abs(signed_circular(float(v),float(w)))) for v,w in zip(p,a)])
                ax=axes[row,0]
                run=0
                for i in range(1,len(x)+1):
                    if i==len(x) or regime_values[i]!=regime_values[run]:
                        ax.axvspan(x[run],x[min(i,len(x)-1)],color=bands[regime_values[run]],zorder=0)
                        run=i
                ax.plot(x,s,color='#263238',lw=1.15)
                # Two explicit bin tracks under the waveform.
                cmap=plt.get_cmap('tab10')
                for y,values in [(-.12,p),(-.28,a)]:
                    identities=[centred_bin(float(v)) for v in values[:-1]]
                    starts=[0]+[i for i in range(1,len(identities)) if identities[i]!=identities[i-1]]
                    ends=starts[1:]+[len(identities)]
                    segments=[[(x[i],y),(x[j],y)] for i,j in zip(starts,ends)]
                    colors=[cmap(identities[i]) for i in starts]
                    ax.add_collection(LineCollection(segments,colors=colors,linewidths=3.5))
                ax.text(-.025,-.12,'φ',ha='right',va='center',fontsize=7.5)
                ax.text(-.025,-.28,'A',ha='right',va='center',fontsize=7.5)
                ax.set_ylim(-.4,1.08);ax.set_yticks([0,.5,1]);ax.set_ylabel('sₙ')
                method_text=' / '.join(methods)
                ax.set_title(f"({chr(97+row)}) {case.label}\nr={case.r:g}; {method_text}",loc='left',pad=5)
                states=axes[row,1]; difference=axes[row,2]
                for method in methods:
                    pp=np.array([phase(float(t),case.r,method) for t in x])
                    color=cyan if method=='single' or group=='extremes' else green
                    ls='--' if method=='single' or group=='extremes' else ':'
                    values=np.array([centred_bin(float(v)) for v in pp]) if discrete else pp
                    states.plot(x,values,color=color,ls=ls,lw=1.15,drawstyle='steps-post' if discrete else 'default')
                    delta=np.array([circular_bin_difference(float(v),float(w)) if discrete else signed_circular(float(v),float(w)) for v,w in zip(pp,a)],dtype=float)
                    # A signed circular branch cut is not interpolated as an ordinary slope.
                    delta[np.r_[False,np.abs(np.diff(delta))>(5 if discrete else .5)]]=np.nan
                    difference.plot(x,delta,color=color,ls=ls,lw=1.05,drawstyle='steps-post' if discrete else 'default')
                aa=np.array([centred_bin(float(v)) for v in a]) if discrete else a
                states.plot(x,aa,color=magenta,lw=1.2,drawstyle='steps-post' if discrete else 'default')
                states.set_ylim((-.4,9.5) if discrete else (-.04,1.04))
                states.set_yticks([0,5,9] if discrete else [0,.5,1])
                states.set_ylabel('Bin index' if discrete else 'State')
                limit=5 if discrete else .5; one=1 if discrete else .1; two=2*one
                for low,high,color in [(-limit,-two,bands[2]),(-two,-one,bands[1]),(-one,one,bands[0]),(one,two,bands[1]),(two,limit,bands[2])]:
                    difference.axhspan(low,high,color=color,zorder=0)
                for v in [-two,-one,one,two]:difference.axhline(v,color='#919994',lw=.4,ls=':')
                difference.axhline(0,color='#444444',lw=.35)
                difference.set_ylim(-limit,limit)
                difference.set_yticks([-5,-2,0,2,5] if discrete else [-.5,-.2,0,.2,.5])
                difference.set_ylabel('δB (bins)' if discrete else 'δ (cycles)')
                selected_row=labels[(case.name,selected)]
                shorthand={0:'Similar',1:'Possible differences',2:'Mostly different'}
                description=shorthand[selected_row['classification']['index']]
                states.set_title('Centred bin functions' if discrete else 'Breath-state functions',fontsize=8.5)
                difference.set_title(f"RMSD={selected_row['circular_rmsd']:.4f}\n{description} ({selected})",fontsize=8.1,pad=4)
                for axis in axes[row]:
                    axis.set_xlim(0,1);axis.set_xticks([0,.5,1]);axis.grid(axis='y',alpha=.18,lw=.4)
                    if row==len(entries)-1:axis.set_xlabel('Normalized cycle time x')
            fig.legend(handles=[Patch(color=cmap(i),label=str(i)) for i in range(10)],
                       loc='lower center',bbox_to_anchor=(.52,.014),ncol=10,frameon=False,
                       title='Centred bin identities on the waveform tracks',fontsize=7,title_fontsize=7.5,
                       handlelength=1.,columnspacing=.85)
            stem=folder/f'{group}-{kind}'
            metadata={'Creator':'Breath State Laboratory synthetic study','Date':None}
            fig.savefig(stem.with_suffix('.svg'),metadata=metadata)
            svg_path=stem.with_suffix('.svg')
            svg_path.write_text('\n'.join(line.rstrip() for line in svg_path.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8')
            fig.savefig(stem.with_suffix('.png'),dpi=300,metadata={'Software':'Breath State Laboratory','Description':'Entirely synthetic ten-bin sorting study'})
            fig.savefig(stem.with_suffix('.pdf'),metadata={'Creator':'Breath State Laboratory','CreationDate':None,'ModDate':None})
            plt.close(fig)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'output/sorting-study')
    parser.add_argument('--plot',action='store_true')
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    report=study_report()
    (args.output/'sorting-study.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    (args.output/'SORTING_RESULTS.md').write_text(markdown(report),encoding='utf-8')
    if args.plot:draw_figures(report,args.output/'figures')
    print(f"Generated {len(report['results'])} independent synthetic comparisons with ten centred bins.")


if __name__=='__main__':main()
