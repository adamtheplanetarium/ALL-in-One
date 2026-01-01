# Email Verification Functions - To be added to gui_mailer.py after reload_from_addresses()

    def refresh_collected_froms(self):
        """Refresh the collected from emails display"""
        try:
            if hasattr(self, 'collected_from_text'):
                self.collected_from_text.delete(1.0, tk.END)
                for email in self.collected_from_emails:
                    status = ""
                    if email in self.verified_froms:
                        status = " ✅ VERIFIED"
                    elif email in self.unverified_froms:
                        status = " ❌ UNVERIFIED"
                    self.collected_from_text.insert(tk.END, f"{email}{status}\n")
                
                # Update stats
                total = len(self.collected_from_emails)
                verified = len(self.verified_froms)
                unverified = len(self.unverified_froms)
                self.verify_stats_label.config(text=f"Collected: {total} | Verified: {verified} | Unverified: {unverified}")
        except Exception as e:
            print(f"{Fore.RED}Error refreshing collected froms: {e}{Style.RESET_ALL}")
    
    def start_verification(self, mode='all'):
        """Start email verification process"""
        if self.verification_in_progress:
            messagebox.showwarning("Verification Running", "Email verification is already in progress!")
            return
        
        # Determine which emails to verify
        if mode == 'all':
            emails_to_verify = list(self.collected_from_emails)
        elif mode == 'verified':
            emails_to_verify = list(self.verified_froms)
        elif mode == 'unverified':
            emails_to_verify = list(self.unverified_froms)
        else:
            emails_to_verify = []
        
        if not emails_to_verify:
            messagebox.showinfo("No Emails", f"No {mode} emails to verify!")
            return
        
        if not self.recipient_email_list:
            messagebox.showerror("No Recipients", "Please add recipients in the Recipients tab first!")
            return
        
        if not self.smtp_servers:
            messagebox.showerror("No SMTP", "Please add SMTP servers first!")
            return
        
        print(f"\n{Fore.GREEN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}🔍 STARTING EMAIL VERIFICATION ({mode.upper()}){Style.RESET_ALL}")
        print(f"{Fore.CYAN}📧 Emails to verify: {len(emails_to_verify)}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}📬 Test recipients: {len(self.recipient_email_list)}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'='*70}{Style.RESET_ALL}\n")
        
        self.monitor_log_print(f"🔍 Starting verification of {len(emails_to_verify)} {mode} emails...", 'info')
        
        # Start verification in background thread
        self.verification_in_progress = True
        verify_thread = threading.Thread(target=self.verification_worker, args=(emails_to_verify,), daemon=True)
        verify_thread.start()
    
    def verification_worker(self, emails_to_verify):
        """Worker thread for email verification"""
        try:
            sent_emails = {}
            
            # Step 1: Send test emails
            print(f"{Fore.YELLOW}📤 Step 1: Sending test emails...{Style.RESET_ALL}")
            self.monitor_log_print("📤 Step 1: Sending test emails...", 'info')
            
            for idx, from_email in enumerate(emails_to_verify, 1):
                if not self.verification_in_progress:
                    break
                
                # Rotate through recipients
                recipient = self.recipient_email_list[idx % len(self.recipient_email_list)]
                
                # Send test email
                success = self.send_test_email(from_email, recipient)
                if success:
                    sent_emails[from_email] = recipient
                    print(f"{Fore.GREEN}  ✓ Sent test from {from_email} to {recipient}{Style.RESET_ALL}")
                    self.monitor_log_print(f"  ✓ Sent test from {from_email}", 'success')
                else:
                    print(f"{Fore.RED}  ✗ Failed to send from {from_email}{Style.RESET_ALL}")
                    self.monitor_log_print(f"  ✗ Failed to send from {from_email}", 'error')
                
                time.sleep(2)  # Small delay between sends
            
            # Step 2: Wait for responses
            wait_time = 120  # Wait 2 minutes
            print(f"\n{Fore.YELLOW}⏳ Step 2: Waiting {wait_time} seconds for responses...{Style.RESET_ALL}")
            self.monitor_log_print(f"⏳ Waiting {wait_time} seconds for email responses...", 'warning')
            
            for i in range(wait_time):
                if not self.verification_in_progress:
                    break
                time.sleep(1)
                if (i + 1) % 30 == 0:
                    print(f"{Fore.CYAN}  ⏱️  {wait_time - i - 1} seconds remaining...{Style.RESET_ALL}")
            
            # Step 3: Check received emails
            print(f"\n{Fore.YELLOW}📥 Step 3: Checking for received emails...{Style.RESET_ALL}")
            self.monitor_log_print("📥 Step 3: Checking received emails...", 'info')
            
            received_froms = self.check_received_emails()
            
            # Step 4: Compare and classify
            print(f"\n{Fore.YELLOW}🔍 Step 4: Verifying emails...{Style.RESET_ALL}")
            
            newly_verified = []
            newly_unverified = []
            
            for from_email in sent_emails.keys():
                if from_email in received_froms:
                    if from_email not in self.verified_froms:
                        self.verified_froms.append(from_email)
                        newly_verified.append(from_email)
                    # Remove from unverified if it was there
                    if from_email in self.unverified_froms:
                        self.unverified_froms.remove(from_email)
                    print(f"{Fore.GREEN}  ✅ VERIFIED: {from_email}{Style.RESET_ALL}")
                else:
                    if from_email not in self.unverified_froms:
                        self.unverified_froms.append(from_email)
                        newly_unverified.append(from_email)
                    # Remove from verified if it was there
                    if from_email in self.verified_froms:
                        self.verified_froms.remove(from_email)
                    print(f"{Fore.RED}  ❌ UNVERIFIED: {from_email}{Style.RESET_ALL}")
            
            # Summary
            print(f"\n{Fore.GREEN}{'='*70}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}📊 VERIFICATION COMPLETE{Style.RESET_ALL}")
            print(f"{Fore.GREEN}✅ Verified: {len(newly_verified)} new, {len(self.verified_froms)} total{Style.RESET_ALL}")
            print(f"{Fore.RED}❌ Unverified: {len(newly_unverified)} new, {len(self.unverified_froms)} total{Style.RESET_ALL}")
            print(f"{Fore.GREEN}{'='*70}{Style.RESET_ALL}\n")
            
            self.monitor_log_print(f"✅ Verification complete: {len(self.verified_froms)} verified, {len(self.unverified_froms)} unverified", 'success')
            
            # Update display
            self.root.after(0, self.refresh_collected_froms)
            self.root.after(0, self.save_config)
            
        except Exception as e:
            print(f"{Fore.RED}❌ Verification error: {e}{Style.RESET_ALL}")
            self.monitor_log_print(f"Error during verification: {e}", 'error')
        finally:
            self.verification_in_progress = False
    
    def send_test_email(self, from_email, recipient):
        """Send a test email for verification"""
        try:
            # Get SMTP server
            if not self.smtp_servers:
                return False
            
            current_smtp = self.smtp_servers[0]  # Use first SMTP for testing
            
            # Connect and send
            server = smtplib.SMTP(current_smtp['host'], current_smtp['port'], timeout=30)
            server.starttls()
            server.login(current_smtp['username'], current_smtp['password'])
            
            # Build test message
            msg = MIMEMultipart()
            msg['From'] = f'Test <{from_email}>'
            msg['To'] = recipient
            msg['Subject'] = f'Verification Test - {datetime.now().strftime("%Y%m%d%H%M%S")}'
            msg.attach(MIMEText(f'Test email from {from_email}', 'plain'))
            
            server.sendmail(current_smtp['username'], [recipient], msg.as_string())
            server.quit()
            
            return True
        except Exception as e:
            print(f"{Fore.RED}Test email error: {e}{Style.RESET_ALL}")
            return False
    
    def check_received_emails(self):
        """Check inbox for received test emails"""
        received_froms = set()
        
        try:
            accounts = self.find_all_inboxes()
            for account in accounts:
                emails = self.parse_inbox_file(account['path'])
                for email in emails:
                    # Extract from address
                    from_addr = self.extract_email_address(email['from'])
                    received_froms.add(from_addr)
        except Exception as e:
            print(f"{Fore.RED}Error checking inbox: {e}{Style.RESET_ALL}")
        
        return received_froms
    
    def save_verified_froms(self):
        """Save verified froms to file"""
        filename = filedialog.asksaveasfilename(title="Save Verified Froms", 
                                               defaultextension=".txt",
                                               filetypes=[("Text files", "*.txt")])
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(self.verified_froms))
                messagebox.showinfo("Success", f"Saved {len(self.verified_froms)} verified emails")
                print(f"{Fore.GREEN}💾 Saved {len(self.verified_froms)} verified froms to {filename}{Style.RESET_ALL}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {e}")
    
    def save_unverified_froms(self):
        """Save unverified froms to file"""
        filename = filedialog.asksaveasfilename(title="Save Unverified Froms", 
                                               defaultextension=".txt",
                                               filetypes=[("Text files", "*.txt")])
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(self.unverified_froms))
                messagebox.showinfo("Success", f"Saved {len(self.unverified_froms)} unverified emails")
                print(f"{Fore.YELLOW}💾 Saved {len(self.unverified_froms)} unverified froms to {filename}{Style.RESET_ALL}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {e}")
    
    def load_verified_froms(self):
        """Load verified froms from file"""
        filename = filedialog.askopenfilename(title="Load Verified Froms", 
                                             filetypes=[("Text files", "*.txt")])
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.verified_froms = [line.strip() for line in f if line.strip()]
                self.refresh_collected_froms()
                messagebox.showinfo("Success", f"Loaded {len(self.verified_froms)} verified emails")
                print(f"{Fore.GREEN}📁 Loaded {len(self.verified_froms)} verified froms{Style.RESET_ALL}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load: {e}")
    
    def load_unverified_froms(self):
        """Load unverified froms from file"""
        filename = filedialog.askopenfilename(title="Load Unverified Froms", 
                                             filetypes=[("Text files", "*.txt")])
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.unverified_froms = [line.strip() for line in f if line.strip()]
                self.refresh_collected_froms()
                messagebox.showinfo("Success", f"Loaded {len(self.unverified_froms)} unverified emails")
                print(f"{Fore.YELLOW}📁 Loaded {len(self.unverified_froms)} unverified froms{Style.RESET_ALL}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load: {e}")
