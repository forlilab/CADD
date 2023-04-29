#
#           AutoDock | Raccoon2
#
#       Copyright 2013, Stefano Forli
#          Molecular Graphics Lab
#
#     The Scripps Research Institute
#           _
#          (,)  T  h e
#         _/
#        (.)    S  c r i p p s
#          \_
#          (,)  R  e s e a r c h
#         ./
#        ( )    I  n s t i t u t e
#         '
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import CADD.Raccoon2
import RaccoonBasics as rb
import RaccoonEvents
import RaccoonServers
import RaccoonServices
import CADD.Raccoon2.HelperFunctionsN3P as hf
import RaccoonProjManTree
import os, Pmw
from PmwOptionMenu import OptionMenu as OptionMenuFix
import Tkinter as tk
import TkTreectrl
import tkMessageBox as tmb
import tkFileDialog as tfd
from PIL import Image, ImageTk
# mgl modules
from mglutil.events import Event, EventHandler
from mglutil.util.callback import CallbackFunction # as cb
import hashlib
import zipfile
import StringIO

#import EF_resultprocessor



class JobManagerTab(rb.TabBase, rb.RaccoonDefaultWidget):
    """ populate and manage the job manager tab """

    def __init__(self, app, parent, debug=False):
        # get
        rb.TabBase.__init__(self, app, debug)
        rb.RaccoonDefaultWidget.__init__(self, parent)
        self.initIcons()
        self.resource = self.app.resource
        # Events
        self.app.eventManager.registerListener(RaccoonEvents.SetResourceEvent, self.handleResource) # set resource
        self.app.eventManager.registerListener(RaccoonEvents.ServerConnection, self._updateRequirementsSsh) # open connection
        #self.app.eventManager.registerListener(RaccoonEvents.UpdateJobHistory, self.updateJobTree)  # job history update
        self.app.eventManager.registerListener(RaccoonEvents.ServiceSelected, self.updateRequirements) # docking service is selected
        self.app.eventManager.registerListener(RaccoonEvents.UserInputRequirementUpdate, self.updateRequirements) # data input (lig,rec...)
        self.app.eventManager.registerListener(RaccoonEvents.SearchConfigChange, self.updateRequirements) # search config change (box)

    def _buildjobman(self):
        """ build the job manager tree"""
        pgroup = Pmw.Group(self.frame, tag_text = 'Jobs', tag_font=self.FONTbold)
        #tk.Button(pgroup.interior(), text='Refresh', image='self.'
        self.jobtree = RaccoonProjManTree.VSresultTree(pgroup.interior(), app = self.app, iconpath=self.iconpath)
        pgroup.pack(expand=1, fill='both', anchor='n', side='bottom')
        self.initJobTree()


    def initJobTree(self, event=None):
        """ populate the tree with the history filer"""
        self.jobtree.setDataFile(self.app.getHistoryFile())

    def initIcons(self):
        """ initialize the icons for the interface"""
        self.iconpath = icon_path = CADD.Raccoon2.ICONPATH
        f = icon_path + os.sep + 'system.png'
        self._ICON_sys = ImageTk.PhotoImage(Image.open(f))
        f = icon_path + os.sep + 'submit.png'
        self._ICON_submit = ImageTk.PhotoImage(Image.open(f))
        f = icon_path + os.sep + 'refresh.png'
        self._ICON_refresh = ImageTk.PhotoImage(Image.open(f))
        f = icon_path + os.sep + 'removex.png'
        self._ICON_removex = ImageTk.PhotoImage(Image.open(f))
        f = icon_path + os.sep + 'remove.png'
        self._ICON_remove = ImageTk.PhotoImage(Image.open(f))
        f = icon_path + os.sep + 'package.png'
        self._ICON_package = ImageTk.PhotoImage(Image.open(f))




    def handleResource(self, event=None):
        self.setResource(event.resource)


    def setResource(self, resource):
        '''adapt the job manager panel to reflect currently selected resource'''
        if resource == 'local':
            self.setLocalResource()
        elif resource == 'cluster':
            self.setClusterResource()
        elif resource == 'opal':
            self.setOpalResource()
        elif resource == 'boinc':
            self.setBoincResource()

    def setLocalResource(self):
        #self.frame.pack_forget()
        self.resetFrame()
        #self.frame = tk.Frame(self.group.interior())

        tk.Label(self.frame, text='(local) requirement widget 1').pack()
        tk.Label(self.frame, text='(local) requirement widget 2').pack()
        tk.Label(self.frame, text='(local) requirement widget 3').pack()
        tk.Label(self.frame, text='SUBMIT').pack()
        self.frame.pack(expand=1, fill='both')


        #print "Raccoon GUI job manager is now on :", self.app.resource

    def setClusterResource(self):
        self.resetFrame()

        #self.frame.configure(bg='red')
        self.group = Pmw.Group(self.frame, tag_text = 'Cluster submission requirements', tag_font=self.FONTbold)
        f = self.group.interior()
        #f.configure(bg='red')

        lwidth = 20
        rwidth = 60
        lbg = '#ffffff'
        rbg = '#ff8888'
        fg = 'black'
        # server connection
        tk.Label(f, text='Server', width=lwidth, font=self.FONT,anchor='e').grid(row=1, column=1,sticky='e',padx=5, pady=0)
        self.reqConn = tk.Label(f, text = '[ click to connect ]', fg = fg, bg=rbg, width=rwidth, font=self.FONT, **self.BORDER)
        self.reqConn.grid(row=1,column=2, sticky='e')
        cb = CallbackFunction(self.switchtab, 'Setup')
        self.reqConn.bind('<Button-1>', cb)

        # XXX self.GUI_LigStatus.bind('<Button-1>', lambda x : self.notebook.selectpage('Ligands'))

        # docking service
        # ligands
        tk.Label(f, text='Docking service', width=lwidth, font=self.FONT,anchor='e').grid(row=2, column=1,sticky='e',padx=5, pady=1)
        self.reqService = tk.Label(f, text = '[ click to select ]', fg = fg, bg=rbg, width=rwidth, font=self.FONT, **self.BORDER)
        self.reqService.grid(row=2,column=2, sticky='w', pady=1)
        cb = CallbackFunction(self.switchtab, 'Setup')
        self.reqService.bind('<Button-1>', cb)


        # ligands
        tk.Label(f, text='Ligands', width=lwidth, font=self.FONT,anchor='e').grid(row=3, column=1,sticky='e',padx=5, pady=1)
        self.reqLig = tk.Label(f, text = '[ click to select ]', fg = fg, bg=rbg, width=rwidth, font=self.FONT, **self.BORDER)
        self.reqLig.grid(row=3,column=2, sticky='w', pady=1)
        cb = CallbackFunction(self.switchtab, 'Ligands')
        self.reqLig.bind('<Button-1>', cb)

        # receptor
        tk.Label(f, text='Receptors', width=lwidth, font=self.FONT,anchor='e').grid(row=5, column=1,sticky='e',padx=5, pady=0)
        self.reqRec = tk.Label(f, text = '[ click to select ]', fg = fg, bg=rbg, width=rwidth, font=self.FONT, **self.BORDER)
        self.reqRec.grid(row=5,column=2, sticky='w')
        cb = CallbackFunction(self.switchtab, 'Receptors')
        self.reqRec.bind('<Button-1>', cb)

        # config
        tk.Label(f, text='Config', width=lwidth, font=self.FONT,anchor='e').grid(row=7, column=1,sticky='e',padx=5, pady=1)
        self.reqConf = tk.Label(f, text = '[ click to select ]', fg = fg, bg=rbg, width=rwidth, font=self.FONT, **self.BORDER)
        self.reqConf.grid(row=7,column=2, sticky='w', pady=1)
        cb = CallbackFunction(self.switchtab, 'Config')
        self.reqConf.bind('<Button-1>', cb)

        # scheduler
        #tk.Label(f, text='Scheduler', width=lwidth, font=self.FONT,anchor='e').grid(row=9, column=1,sticky='e',padx=5, pady=0)
        #self.reqSched = tk.Label(f, text = '[ click to select ]', fg = fg, bg=rbg, width=rwidth, font=self.FONT, **self.BORDER)
        #self.reqSched.grid(row=9,column=2, sticky='w')
        #cb = CallbackFunction(self.switchtab, 'Setup')
        #self.reqSched.bind('<Button-1>', cb)

        # submission
        self.SubmitButton = tk.Button(f, text = 'Submit...', image=self._ICON_submit,
            font=self.FONT, compound='left',state='disabled', command=self.submit, **self.BORDER)
        self.SubmitButton.grid(row=20, column=1, sticky='we', columnspan=3, padx=4, pady=3)

        self.group.pack(fill='none',side='top', anchor='w', ipadx=5, ipady=5)

        self._buildjobman()

        self.frame.pack(expand=1, fill='both',anchor='n')
        self._updateRequirementsSsh()

        #print "Raccoon GUI job manager is now on :", self.app.resource


    def switchtab(self, tab, event=None):
        """ """
        self.app.notebook.selectpage(tab)

    def setOpalResource(self):
        self.resetFrame()
        self.frame = tk.Frame(self.group.interior())
        tk.Label(self.frame, text='(opal) requirement widget 1').pack()
        tk.Label(self.frame, text='(opal) requirement widget 2').pack()
        tk.Label(self.frame, text='(opal) requirement widget 3').pack()
        self.frame.pack(expand=1, fill='both')
        #print "Raccoon GUI job manager is now on :", self.app.resource

    def setBoincResource(self):
        bset = { 'bg' : '#969b9d'  } # 'width' : 22, 'height': 22, 'relief' : 'raised'}
        bset = {}
        bset.update(self.BORDER)
        self.resetFrame()

        self.group_new_batch = Pmw.Group(self.frame, tag_text = 'New docking batch', tag_font=self.FONTbold)
        f = self.group_new_batch.interior()
        self.ligLabel = tk.Label(f, text='Ligands: %s' % len(self.app.engine.LigBook))
        self.ligLabel.pack(anchor='w', side='left',padx=1)
        self.recLabel = tk.Label(f, text='Receptors: %s' % len(self.app.engine.RecBook))
        self.recLabel.pack(anchor='w', side='left',padx=1)
        self.tasksLabel = tk.Label(f, text='Tasks:')
        self.tasksLabel = tk.Label(f, text='Tasks: %s' % (len(self.app.engine.LigBook) * len(self.app.engine.RecBook)))
        self.tasksLabel.pack(anchor='w', side='left',padx=1)
        self.SubmitButton = tk.Button(f, text = 'Submit', image=self._ICON_submit,
            font=self.FONT, compound='left', state='disabled', command=self.submit_boinc, **self.BORDER)
        self.SubmitButton.pack(anchor='w', side='left',padx=0)
        self.group_new_batch.pack(fill='x',side='top', anchor='w', ipadx=5, ipady=5)

        self.group_batches = Pmw.Group(self.frame, tag_text = 'Batches', tag_font=self.FONTbold)
        f = self.group_batches.interior()

        toolb = tk.Frame(f)
        if self.sysarch == 'Windows':
            bwidth = 54
        else:
            bwidth = 32
        b = tk.Button(toolb, text='Refresh', compound='top', image = self._ICON_refresh, command=self.refreshBatchesBoinc, width=bwidth, font=self.FONTbold, **bset )
        b.pack(anchor='n', side='top')
        b = tk.Button(toolb, text='Abort', compound='top', image = self._ICON_removex, command=self.abortBatchBoinc, width=bwidth, font=self.FONTbold, **bset )
        b.pack(anchor='n', side='top')
        b = tk.Button(toolb, text='Download', compound='top', image = self._ICON_package, command=self.downloadResultsBoinc, width=bwidth, font=self.FONTbold, **bset )
        b.pack(anchor='n', side='top')
        b = tk.Button(toolb, text='Delete', compound='top', image = self._ICON_remove, command=self.retireBatchBoinc, width=bwidth, font=self.FONTbold, **bset )
        b.pack(anchor='n', side='top')
        toolb.pack(side='left', anchor='w', expand=0, fill='y',pady=0)

        self.batchManager = TkTreectrl.ScrolledMultiListbox(f, bd=2)
        self.batchManager.listbox.config(bg='white', fg='black', font=self.FONT,
                   columns = ('id', 'name', 'state', 'done', 'jobs', 'failed jobs'),
                   selectmode='extended',
                              )
        self.batchManager.pack(anchor='w', side='left', expand=1, fill='both')

        self.group_batches.pack(fill='both',side='top', anchor='w', expand='1', ipadx=5, ipady=5)

        self.frame.pack(expand=1, fill='both', anchor='n')

    def updateRequirements(self, event=None):
        """ update submission requirements """
        if self.app.resource == 'local':
            self._updateRequirementsLocal(event)
        elif self.app.resource == 'cluster':
            self._updateRequirementsSsh(event)
        elif self.app.resource == 'opal':
            self._updateRequirementsOpal(event)
        elif self.app.resource == 'boinc':
            self._updateRequirementsBoinc(event)

    def submit(self, event=None, suggest={}):
        jsub = JobSubmissionInterface(self.frame, jmanager=self.jobtree, app = self.app, suggest=suggest)
        job_info = jsub.getinfo()
        self.app.setBusy()
        if job_info == None:
            self.app.setReady()
            return
        if self.app.resource == 'local':
            self.submit_local(job_info)
        elif self.app.resource == 'cluster':
            self.submit_cluster(job_info)
        elif self.app.resource == 'opal':
            self.submit_opal(job_info)
        self.app.setReady()

    def submit_local(self, job_info):
        """ manage submission and feedback from local resource"""
        report = self.app.submitLocal(job_info)

    def submit_opal(self, job_info):
        """ manage submission and feedback from Opal resource"""
        report = self.app.submitOpal(job_info)

    def submit_cluster(self, job_info):
        """ manage submission and feedback from Ssh cluster resource"""
        # report = { 'submissions': [], 'server_duplicates' : [], 'local_duplicates' : [] }
        report = self.app.testSshJobs(job_info)
        sdup = report['server_duplicates']
        ldup = report['local_duplicates']
        choice = 'skip'
        #print "\n\n\nREPORT FOR DUPLICATES", report
        #print "\n\n\n"
        if len(sdup) or len(ldup):
            #print "WE HAVE DUPLICATES>", len(sdup), len(ldup)
            choice = ManageJobOverlaps(self.frame, report)
            #buttons = ('Skip', 'Modify tag', 'Auto-rename', 'Overwrite', 'Cancel'),
            if choice == 'tag':
                t = 'Submission'
                i = 'info'
                m = 'Repeat the submission specifying a different tag.'
                tmb.showinfo(parent=self.frame, title=t, message=m, icon=i)
                return
        # XXX close here the job submission manager
        if choice == 'cancel':
            return

        self.app.setBusy()
        submission = self.app.submitSsh(job_info, duplicates=choice)
        s = len(submission)
        if s>0:
            t = 'Submission'
            i = 'info'
            m = '%d jobs submitted successfully.' % (s / 2)
            tmb.showinfo(parent=self.frame, title=t, message=m, icon=i)
            self.app.setReady()
            return True
        else:
            t = 'Submission'
            i = 'error'
            m = 'No jobs have been submitted!'
            tmb.showinfo(parent=self.frame, title=t, message=m, icon=i)
            self.app.setReady()
            return False

    def abortBatchBoinc(self):
        """ abort a batch of jobs on boinc """
        if tmb.askyesno('Abort batch', 'Are you sure you want to abort the selected batch(es)?\nAll jobs in the batch(es) will be aborted.'):
            sel = self.batchManager.listbox.curselection()
            if len(sel) == 0:
                return
            for s in sel:
                batch_id = self.batchManager.listbox.get(s)[0][0]
                self._abort_batch_boinc(batch_id)
            self.refreshBatchesBoinc()

    def retireBatchBoinc(self):
        """ retire a batch of jobs on boinc """
        if tmb.askyesno('Delete batch', 'Are you sure you want to delete the selected batch(es)?\nAll results will be removed.'):
            sel = self.batchManager.listbox.curselection()
            if len(sel) == 0:
                return
            for s in sel:
                batch_id = self.batchManager.listbox.get(s)[0][0]
                self._retire_batch_boinc(batch_id)
            self.refreshBatchesBoinc()

    def refreshBatchesBoinc(self):
        """ get the list of batches from the boinc server """
        self.batchManager.listbox.delete(0, 'end')

        if self.app.boincService.isAuthenticated() == False:
            tmb.showerror('Submission', 'You are not authenticated to the BOINC server. Please login first.')
            return

        result, message, batches = self.app.boincService.queryBatches()
        if result == False:
            tmb.showerror('Submission', message)
            return False

        for batch in batches:
            if batch.state == '0':
                state = 'New'
            elif batch.state == '1':
                state = 'In progress'
            elif batch.state == '2':
                state = 'Completed'
            elif batch.state == '3':
                state = 'Aborted'
            elif batch.state == '4':
                state = 'Retired'
            else:
                state = 'Unknown'
            done = str(float(batch.fraction_done) * 100) + '%'
            self.batchManager.listbox.insert('END', batch.id, batch.name, state, done, batch.njobs, batch.nerror_jobs)

    def submit_boinc(self):
        """ submit a batch of jobs to the boinc server"""
        if self.app.boincService.isAuthenticated() == False:
            tmb.showerror('Submission', 'You are not authenticated to the BOINC server. Please login first.')
            return False

        func = self._submit_batch_boinc
        func_kwargs = { }
        progressWin = rb.ProgressDialogWindowTk(parent = self.frame,
                function = func, func_kwargs = func_kwargs,
                title ='Jobs Processing', message = "Submitting jobs to BOINC server...",
                operation = 'submitting jobs',
                image = None, autoclose=True, progresstype='percent')
        progressWin.start()
        self.app.setReady()
        if progressWin._STOP or (not progressWin._COMPLETED) or progressWin.getOutput() == False:
            return False

        tmb.showinfo('Submission', 'Jobs submitted successfully.')
        self.refreshBatchesBoinc()

        return True

    def downloadResultsBoinc(self):
        """ download the results of a batch of jobs from the boinc server"""
        if not tmb.askyesno('Download', 'Are you sure you want to download results of the selected batch(es)?'):
            return
        outdir = tfd.askdirectory(parent=self.frame, title='Select a directory to save the results')
        if not outdir:
            return

        sel = self.batchManager.listbox.curselection()
        if len(sel) == 0:
            return
        for s in sel:
            batch_id = self.batchManager.listbox.get(s)[0][0]

            func = self._download_results_boinc
            func_kwargs = { 'batch_id':batch_id, 'outdir':outdir }
            progressWin = rb.ProgressDialogWindowTk(parent = self.frame,
                    function = func, func_kwargs = func_kwargs,
                    title ='Results Downloading', message = "Downloading results from the BOINC server...",
                    operation = 'downloading results',
                    image = None, autoclose=True, progresstype=None)
            progressWin.start()
            self.app.setReady()
            if progressWin._STOP or (not progressWin._COMPLETED) or progressWin.getOutput() == False:
                return False

            zipfilename = progressWin.getOutput()
            func = self._unzip_results_boinc
            func_kwargs = { 'zipfilename':zipfilename, 'outdir':outdir }
            progressWin = rb.ProgressDialogWindowTk(parent = self.frame,
                    function = func, func_kwargs = func_kwargs,
                    title ='Results Unzipping', message = "Unzipping downloaded results...",
                    operation = 'unzipping results',
                    image = None, autoclose=True, progresstype='percent')
            progressWin.start()
            self.app.setReady()
            if progressWin._STOP or (not progressWin._COMPLETED) or progressWin.getOutput() == False:
                return False

            os.remove(zipfilename)
            tmb.showinfo('Download', 'Results downloaded successfully.')

    def _unzip_results_boinc(self, zipfilename, outdir, GUI = None, stopcheck = None, showpercent=None):
        """ unzip the results of a batch of jobs """
        zip_file = zipfile.ZipFile(zipfilename)
        namelist = zip_file.namelist()
        total = len(namelist)
        processed = 0
        for name in namelist:
            if stopcheck != None and stopcheck():
                zip_file.close()
                return False
            if showpercent != None:
                showpercent(hf.percent(processed, total))
            if GUI != None:
                GUI.update()
            buff = zip_file.read(name)
            sub_zip_file = zipfile.ZipFile(StringIO.StringIO(buff))
            sub_zip_file.extractall(outdir)
            sub_zip_file.close()
            processed += 1
        zip_file.close()
        if showpercent != None:
                showpercent(hf.percent(total, total))
        return True

    def _download_results_boinc(self, batch_id, outdir, GUI = None, stopcheck = None, showpercent=None):
        result, message = self.app.boincService.downloadResults(batch_id, outdir)
        if result == False:
            tmb.showerror('Download', message)
            return False
        return message

    def _abort_batch_boinc(self, batch_id):
        result, message = self.app.boincService.abortBatch(batch_id)
        if result == False:
            tmb.showerror('Submission', message)
            return False
        return True

    def _retire_batch_boinc(self, batch_id):
        result, message = self.app.boincService.retireBatch(batch_id)
        if result == False:
            tmb.showerror('Submission', message)
            return False
        return True

    def _submit_batch_boinc(self, GUI = None, stopcheck = None, showpercent=None):
        total = 2 + len(self.app.engine.ligands()) * len(self.app.engine.receptors())

        result, message, batch_id = self.app.boincService.createBatch()
        if result == False:
            tmb.showerror('Submission', message)
            return False

        # update progress
        if showpercent != None:
            showpercent(hf.percent(1, total))

        processed = 0
        processed_files = []
        for rec in self.app.engine.receptors():
            for lig in self.app.engine.ligands():
                # check stop
                if stopcheck != None and stopcheck():
                    return False
                # update progress
                if showpercent != None:
                    showpercent(hf.percent(processed + 1, total))
                # update GUI
                if GUI != None:
                    GUI.update()

                json_document = self.app.engine.generateBoincTaskJson(rec, lig, self.app.dockengine, self.app.configTab)
                if json_document == None:
                    continue
                zip_file_path = self.app.engine.generateBoincTaskZip(rec, lig, json_document)
                json_document_hash = str(hashlib.md5(json_document).hexdigest())
                boinc_file_name = ('%s_%s_%s.zip') % (batch_id, processed, json_document_hash)
                processed_files.append(boinc_file_name)

                if not self.app.boincService.uploadFile(batch_id, zip_file_path, boinc_file_name):
                    tmb.showerror('Submission', 'Error uploading files to BOINC server.')
                    os.remove(zip_file_path)
                    self._abort_batch_boinc(batch_id)
                    self._retire_batch_boinc(batch_id)
                    return False

                os.remove(zip_file_path)
                processed = processed + 1

        # update progress
        if showpercent != None:
            showpercent(hf.percent(processed + 1, total))

        result, message = self.app.boincService.submitBatch(batch_id, processed_files)
        if result == False:
            self._abort_batch_boinc(batch_id)
            self._retire_batch_boinc(batch_id)
            tmb.showerror('Submission', message)
            return False

        # update progress
        if showpercent != None:
            showpercent(hf.percent(total, total))

        return True

    def _updateRequirementsLocal(self, event=None):
        """ update the check for requirements
            of local submission
        """
        _type = event._type
        pass


    def _updateRequirementsSsh(self, event=None):
        """ update the check for requirements
            of ssh submission
        """
        g = 'black'
        r = 'red'
        d = '[ click to select ]'
        green = '#99ff44'
        red = '#ff4444'
        orange = '#ffcc44'

        missing = False
        #_type = event._type
        # check connection
        if not self.app.server == None:
            t = "connected to %s" % self.app.server.properties['name']
            # check racconized
            if self.app.server.properties['ready']:
                self.reqConn.configure(text = t, bg = green)
            else:
                t = "connected to %s (NOT RACCONIZED!)" % self.app.server.properties['name']
                self.reqConn.configure(text = t, bg = orange)
                missing = True
        else:
            missing = True
            self.reqConn.configure(text = d, bg = red)

        if not self.app.dockingservice == None:
            t = '%s' % self.app.dockingservice
            self.reqService.configure(text = t, bg = green)
        else:
            missing = True
            self.reqService.configure(text = d, bg = red)

        # ligand
        if len(self.app.ligand_source):
            libnames = ",".join([x['lib'].name() for x in self.app.ligand_source])
            t = "library selected (%s)" % libnames
            self.reqLig.configure(fg = g, text = t, bg = green)
        else:
            missing = True
            self.reqLig.configure(fg = g, text = d, bg = red)
        # rec
        if len(self.app.engine.receptors()) > 0:
            t = "%s receptors selected" % len(self.app.engine.receptors())
            self.reqRec.configure(fg = g, text = t, bg = green)
        else:
            missing = True
            self.reqRec.configure(fg = g, text = d, bg = red)
        # conf
        conf = self.app.engine.gridBox()
        if not None in conf['center'] + conf['size']:
            t = "search box defined"
            self.reqConf.configure(fg = g, text = t, bg = green)
            c = g
        else:
            missing = True
            self.reqConf.configure(fg = g, text = d, bg = red)
        # sched
        #if not self.app.server == None:
        #    sched = self.app.server.systemInfo('scheduler')
        #else:
        #    missing = True
        # submit
        if not missing:
            self.SubmitButton.configure(state='normal')

    def _updateRequirementsOpal(self, event=None):
        """ update the check for requirements
            of opal submission
        """
        _type = event._type
        pass

    def _updateRequirementsBoinc(self, event=None):
        """ update the check for requirements
            of boinc submission
        """
        ligCount = len(self.app.engine.LigBook)
        recCount = len(self.app.engine.RecBook)
        tasksCount = ligCount * recCount
        self.ligLabel.configure(text = 'Ligands: %s' % ligCount)
        self.recLabel.configure(text = 'Receptors: %s' % recCount)
        self.tasksLabel.configure(text = 'Tasks: %s' % tasksCount)
        if tasksCount > 0:
            self.SubmitButton.configure(state = 'normal')
        else:
            self.SubmitButton.configure(state = 'disabled')

class JobSubmissionInterface(rb.RaccoonDefaultWidget):
    """ ask for Project, Exp, VS info..."""

    def __init__(self, parent, jmanager, app, suggest={}):
        """ parent      : tkparent
            jmanager    : job manager tree (to query current prj,exp...)
            app         : containing app
        """
        rb.RaccoonDefaultWidget.__init__(self, parent)
        self.jmanager = jmanager
        self.app = app
        self._new = '<new>'
        self.jobdata = None
        self.suggest = suggest
        self.initIcons()
        self.build()

    def initIcons(self):
        pass

    def close(self, result):
        """ close the window and decides what to do
            if OK requested, check values and start submission
        """
        if result == 'OK':
            if not self.checkinfo():
                return
            p = self.getPrj()
            e = self.getExp()
            t = self.tag_entry.getvalue().strip()
            self.jobdata = {'prj' : p, 'exp': e, 'tag':t}
            self.win.deactivate(self.jobdata)
        else:
            self.win.deactivate(False)

    def getPrj(self):
        """ return the project name"""
        m = ('The project name is not valid.\n')
        p = self.prj_pull.getvalue() # old project
        if p == self._new:
            if not self.prj_new.valid():
                self.errorMsg(m)
                return False
            p = self.prj_new.getvalue()
        return p

    def getExp(self):
        """ return the experiment name"""
        m = ('The experiment name is not valid.\n')
        e = self.exp_pull.getvalue() # old project
        if e == self._new:
            if not self.exp_new.valid():
                self.errorMsg(m)
                return False
            e = self.exp_new.getvalue()
        return e

    def getTag(self):
        """ return the tag"""
        tag = self.tag_entry.getvalue()
        return tag


    def checkDuplicates(self):
        """ check that the jobs that are going to be
            submitted do not have the same name of
            already submitted jobs
        """
        m = ('The submission cannot be performed because there '
             'are already jobs with the same name stored in project %s '
             '/experiment %s.\n\n'
             'Either create new project/experiments or use a different tag.')
        job_info = {'prj' : self.getPrj(),
                    'exp' : self.getExp(),
                    'tag' : self.getTag()
                   }
        report = self.app.testSshJobs(job_info)
        e = []
        if len(report['server_duplicates']):
            e.append('the current server')
        if len(report['local_duplicates']):
            e.append('the local client')
        if len(e):
            m = m % ( job_info['prj'], job_info['exp'])
            self.errorMsg(m)
            return False
        return True

    def checkinfo(self):
        """ check that user provided info are valid"""
        if not self.getPrj():
            return False
        if not self.getExp():
            return False
        if not self.checkDuplicates():
            return False
        return True


    def errorMsg(self, message):
        """ display submission entries error"""
        t = 'Incorrect name entry'
        i = 'error'
        tmb.showinfo(parent=self.win.interior(), title=t, message=message, icon=i)
        return


    def getinfo(self):
        """ return the user provided info"""
        return self.jobdata


    def _setprjname(self, event=None):
        choice = self.prj_pull.getvalue()
        if choice == self._new:
            self.prj_new.grid(row=4, column=2, sticky='we',padx=4,pady=4)
            self.prj_new.checkentry()
        else:
            self.prj_new.grid_forget()
        exp_list = self._getexplist()
        self.exp_pull.setitems( exp_list )
        self.exp_pull.setvalue( exp_list[-1])
        self.exp_pull.invoke()

    def _getexplist(self, event=None):
        prj = self.prj_pull.getvalue()
        if prj == self._new:
            return [self._new]
        else:
            exp_list = sorted(self.info[prj].keys())
            return exp_list + [self._new]

    def _setexpname(self, event=None):
        choice = self.exp_pull.getvalue()
        if choice == self._new:
            self.exp_new.grid(row=8,column=2, sticky='we', padx=4,pady=4)
            self.exp_new.checkentry()
        else:
            self.exp_new.grid_forget()

    def build(self):
        # get info from the current manager
        self.info = self.jmanager.getTreeGraph()
        self.prj_list = sorted(self.info.keys()) + [self._new]
        #self.prj_list.append(self._new)
        self.win = Pmw.Dialog(parent=self.parent, buttons=('OK', 'Cancel'),
            title = 'Submit jobs', command = self.close)
        w = self.win.interior()
        bbox = self.win.component('buttonbox')
        for i in range(bbox.numbuttons()):
            bbox.button(i).configure(font=self.FONT, default='disabled', **self.BORDER)

        tk.Label(w, text='Select the new VS properties', font=self.FONT).grid(row=0,column=1, sticky='we', columnspan=3,padx=5,pady=5)
        tk.Frame(w,height=2,bd=1,relief='sunken').grid(row=1, column=0, sticky='ew', columnspan=3, pady=3)
        # project
        tk.Label(w, text='Project', font=self.FONTbold, width=12,anchor='e').grid(row=3,column=1,sticky='we')
        tk.Label(w, text='', font=self.FONT, width=10).grid(row=4,column=1,sticky='we',pady=5) # placeholder for entry

        self.prj_pull = OptionMenuFix(w,
               menubutton_width=30,
               menubutton_font=self.FONT,
               menu_font=self.FONT,
               menubutton_bd = 1, menubutton_highlightbackground = 'black',
               menubutton_borderwidth=1, menubutton_highlightcolor='black',
               menubutton_highlightthickness = 1,
               menubutton_height=1,
               items = self.prj_list,
               initialitem=-1,
               command = self._setprjname)
        self.prj_pull.grid(row=3,column=2,sticky='we',padx=3)

        self.prj_new = Pmw.EntryField(w, value='', validate = {'validator' : hf.validateAscii, 'minstrict': 0}) #,
        self.prj_new.component('entry').configure(justify='left', font=self.FONT, bg='pink',width=33, **self.BORDER)

        # --------------------------------
        tk.Frame(w,height=2,bd=1,relief='sunken').grid(row=6, column=0, sticky='ew', columnspan=3, pady=3)

        # experiment
        tk.Label(w, text='Experiment', font=self.FONTbold, width=12,anchor='e').grid(row=7,column=1,sticky='we')
        tk.Label(w, text='', font=self.FONT, width=10).grid(row=8,column=1,sticky='we',pady=5) # placeholder for entry

        self.exp_pull = OptionMenuFix(w,labelpos='w',
                       menubutton_width=30,
                       menubutton_font=self.FONT,
                       menu_font=self.FONT,
               menubutton_bd = 1, menubutton_highlightbackground = 'black',
               menubutton_borderwidth=1, menubutton_highlightcolor='black',
               menubutton_highlightthickness = 1,
               menubutton_height=1,
                       items=[self._new],
                       initialitem=-1,
                       command = self._setexpname)
        self.exp_pull.grid(row=7, column =2, sticky='we',padx=3)
        self.exp_new = Pmw.EntryField(w, value='', validate = {'validator' : hf.validateAscii, 'minstrict':0}) #,
        self.exp_new.component('entry').configure(justify='left', font=self.FONT, bg='pink',width=30, **self.BORDER)
        # initialize the interface with the projects
        self._setprjname()
        self.prj_pull.setvalue( self.prj_list[-1])

        # --------------------------------
        tk.Frame(w,height=2,bd=1,relief='sunken').grid(row=9, column=0, sticky='ew', columnspan=3, pady=3)
        # job tag
        tk.Label(w, text='Optional jobs name tag', font=self.FONT).grid(row=10, column=1,columnspan=3,sticky='we',padx=5)
        self.tag_entry = Pmw.EntryField(w, value='', validate = hf.validateAsciiEmpty) #,
        self.tag_entry.component('entry').configure(justify='left', font=self.FONT, bg='white',width=30, **self.BORDER)
        self.tag_entry.grid(row=11,column=1, columnspan=3, sticky='we', padx=4,pady=4)

        self.win.bind('<Escape>', self.close)
        self.setSuggest()
        self.win.activate()


    def setSuggest(self):
        """ fill the submission with the suggestions"""
        if self.suggest == {}:
            return
        if 'prj' in self.suggest.keys():
            prj = self.suggest.pop('prj')
            self.prj_pull.setvalue(prj)
            self.prj_pull.invoke()
        if 'exp' in self.suggest.keys():
            exp = self.suggest.pop('exp')
            self.exp_pull.setvalue(exp)
            self.exp_pull.invoke()
        if 'tag' in self.suggest.keys():
            tag = self.suggest.pop('tag')
        else:
            tag = 'RESTARTED'
        self.tag_entry.setvalue(tag)




class ManageJobOverlaps(rb.RaccoonDefaultWidget):


    def __init__(self, parent, duplicates):
        rb.RaccoonDefaultWidget.__init__(self, parent)
        self.count = count
        #self.names = names
        self.remotenames = duplicates['server_duplicates']
        self.localnames = duplicates['local_duplicates']
        self.dialog = Pmw.Dialog(parent,
            buttons = ('Skip', 'Modify tag', 'Auto-rename', 'Overwrite', 'Cancel'),
            default_button = 'Modify tag',
            title = 'Jobs naming issues',
            command = self.execute)
        self.dialog.withdraw()
        d = self.dialog.interior()

        msg = ("The following jobs to be generated are going to "
               "overwrite jobs with the same names already "
               "present on the server.")
        pack_def = { 'side': 'top', 'anchor':'n', 'expand':0, 'fill':'x'}
        tk.Label(d, text = msg).pack(**pack_def)
        if len(self.remotenames):
            slb = Pmw.ScrolledListBox(d, listbox_font=self.FONT, items = self.remotenames,
                label_text = 'Server job names', labelpos='nw', label_font=self.FONTbold,
                listbox_selectmode='EXTENDED')
            slb.pack(side='left', anchor='w', expand='1', fill='both')
        if len(self.localnames):
            llb = Pmw.ScrolledListBox(d, listbox_font=self.FONT, items = self.localnames,
                label_text = 'Local job names', labelpos='nw', label_font=self.FONTbold,
                listbox_selectmode='EXTENDED')
            llb.pack(side='left', anchor='w', expand='1', fill='both')
        self.dialog.activate(globalMode=1)


    def execute(self, result):
        if result == 'Overwrite':
            t = 'Overwrite jobs'
            i = 'warning'
            m = ('Are you sure you want to overwrite %d jobs?' % len(names) )
            if not tmb.askyesno(parent=self.parent, title=t, icon=i, message=m):
                return
            choice == 'overwrite'
        elif result == 'Skip':
            choice = 'skip'
        elif result == 'Modify tag':
            choice = 'tag'
        elif result == 'Auto-rename':
            choice = 'rename'
        elif result == 'Cancel':
            choice = 'cancel'
        self.dialog.deactivate(choice)

