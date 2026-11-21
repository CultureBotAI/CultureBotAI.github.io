#!/usr/bin/env python3
"""Exercise populated ProteinTraits listing controls for Nov19 feature review.

Inputs: live public Pages. Output: new owned controls receipt, no mutations.
Resolves sorting/full-catalogue coverage gaps in the primary browser receipt.
"""
import json
from revalidate_group_b_20261119 import OUT,CHROME,now,deployment,settle,ACTION_JS
from playwright.sync_api import sync_playwright

def main():
    dest=OUT/'proteintraitsmech-controls.json'
    if dest.exists():raise SystemExit('Refusing overwrite: '+str(dest))
    base='https://culturebotai.github.io/proteintraitsmech/'
    report={'started_at':now(),'deployment_before':deployment('proteintraitsmech',base),'checks':{}}
    def save():dest.write_text(json.dumps(report,indent=2)+'\n')
    save()
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=CHROME,headless=True)
        page=browser.new_page(viewport={'width':1280,'height':900})
        page.goto(base+'browse.html',wait_until='networkidle',timeout=90000)
        settle(page,'ProteinTraitsMech')
        page.get_by_role('button',name='Show all (5)',exact=True).click()
        for axis in ['FUNCTION','SEQUENCE','STRUCTURE','SEQUENCE_STRUCTURE','EVOLUTION']:
            page.locator(f'label:has(input[data-facet="axis"][value="{axis}"])').click()
            settle(page,'ProteinTraitsMech')
        report['checks']['all_axes']=page.evaluate(ACTION_JS);save()
        page.locator('#clear-facets').click();settle(page,'ProteinTraitsMech')
        report['checks']['reset']=page.evaluate(ACTION_JS)
        page.locator('#q').fill('homogentisate 1,2-dioxygenase');settle(page,'ProteinTraitsMech')
        report['checks']['sort_orders']={}
        for value in ['id','label','label-desc','axis','source']:
            page.locator('#sort').select_option(value);settle(page,'ProteinTraitsMech')
            report['checks']['sort_orders'][value]=page.evaluate(ACTION_JS)|{'result_text':page.locator('#results').inner_text()}
            save()
        browser.close()
    report['deployment_after']=deployment('proteintraitsmech',base)
    assert report['deployment_before']['id']==report['deployment_after']['id']
    report['complete']=True;report['finished_at']=now();save()
    print(json.dumps({'complete':True,'path':str(dest)}))

if __name__=='__main__':main()
