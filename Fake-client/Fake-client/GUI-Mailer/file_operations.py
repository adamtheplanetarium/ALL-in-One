"""
File Operations Module
Handles all file load/save operations for GUI Mailer
"""
import tkinter as tk
from tkinter import filedialog, messagebox
import os
from colorama import Fore, Style

class FileOperations:
    """Handles all file I/O operations"""
    
    @staticmethod
    def load_smtp_file(gui_instance):
        filename = filedialog.askopenfilename(title="Load SMTP Servers", 
                                             filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                gui_instance.smtp_text.delete(1.0, tk.END)
                gui_instance.smtp_text.insert(1.0, content)
                gui_instance.log_message(f"Loaded SMTP servers from: {filename}", 'info')
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")
                
    @staticmethod
    def save_smtp_file(gui_instance):
        filename = filedialog.asksaveasfilename(title="Save SMTP Servers", 
                                               defaultextension=".txt",
                                               filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(gui_instance.smtp_text.get(1.0, tk.END))
                gui_instance.log_message(f"Saved SMTP servers to: {filename}", 'info')
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")
                
    @staticmethod
    def load_recipients_file(gui_instance):
        filename = filedialog.askopenfilename(title="Load Recipients", 
                                             filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                gui_instance.recipients_text.delete(1.0, tk.END)
                gui_instance.recipients_text.insert(1.0, content)
                gui_instance.log_message(f"Loaded recipients from: {filename}", 'info')
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")
                
    @staticmethod
    def save_recipients_file(gui_instance):
        filename = filedialog.asksaveasfilename(title="Save Recipients", 
                                               defaultextension=".txt",
                                               filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(gui_instance.recipients_text.get(1.0, tk.END))
                gui_instance.log_message(f"Saved recipients to: {filename}", 'info')
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")
                
    @staticmethod
    def load_from_file(gui_instance):
        filename = filedialog.askopenfilename(title="Load From Addresses", 
                                             filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if filename:
            try:
                # Check file size first
                import os
                file_size = os.path.getsize(filename)
                file_size_mb = file_size / (1024 * 1024)
                
                if file_size_mb > 50:
                    result = messagebox.askyesno(
                        "Large File Warning",
                        f"File is {file_size_mb:.1f} MB!\n\n"
                        f"Loading huge files may take time.\n\n"
                        f"Load first 500,000 lines only?",
                        icon='warning'
                    )
                    
                    if result:
                        # Load only first 500K lines
                        gui_instance.log_message(f"Loading first 500,000 lines from: {filename}", 'info')
                        with open(filename, 'r', encoding='utf-8') as f:
                            lines = []
                            for i, line in enumerate(f):
                                if i >= 500000:
                                    break
                                lines.append(line)
                            content = ''.join(lines)
                        gui_instance.log_message(f"Loaded 500,000 lines", 'success')
                        messagebox.showinfo("Loaded", "Loaded first 500,000 lines successfully!")
                    else:
                        return
                elif file_size_mb > 10:
                    # Medium file - load with progress
                    gui_instance.log_message(f"Loading {file_size_mb:.1f} MB file...", 'info')
                    with open(filename, 'r', encoding='utf-8') as f:
                        content = f.read()
                    gui_instance.log_message(f"Loaded successfully", 'success')
                else:
                    with open(filename, 'r', encoding='utf-8') as f:
                        content = f.read()
                    gui_instance.log_message(f"Loaded from addresses from: {filename}", 'info')
                
                # Load into textarea
                gui_instance.from_text.delete(1.0, tk.END)
                gui_instance.from_text.insert(1.0, content)
                
                # Show count
                line_count = content.count('\n')
                if line_count > 200000:
                    gui_instance.console_print(f"[INFO] Loaded {line_count:,} lines - This is a large file!", 'cyan')
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")
                
    @staticmethod
    def save_from_file(gui_instance):
        filename = filedialog.asksaveasfilename(title="Save From Addresses", 
                                               defaultextension=".txt",
                                               filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(gui_instance.from_text.get(1.0, tk.END))
                gui_instance.log_message(f"Saved from addresses to: {filename}", 'info')
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")
                
    @staticmethod
    def load_template_file(gui_instance):
        filename = filedialog.askopenfilename(title="Load Email Template", 
                                             filetypes=[("HTML files", "*.html *.htm"), ("Text files", "*.txt"), ("All files", "*.*")])
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                gui_instance.template_text.delete(1.0, tk.END)
                gui_instance.template_text.insert(1.0, content)
                gui_instance.log_message(f"Loaded template from: {filename}", 'info')
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")
                
    @staticmethod
    def save_template_file(gui_instance):
        filename = filedialog.asksaveasfilename(title="Save Email Template", 
                                               defaultextension=".html",
                                               filetypes=[("HTML files", "*.html"), ("All files", "*.*")])
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(gui_instance.template_text.get(1.0, tk.END))
                gui_instance.log_message(f"Saved template to: {filename}", 'info')
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")
    
    @staticmethod
    def save_from_address(gui_instance, email_address):
        """Save email address to from.txt and update counter"""
        try:
            # Append to from.txt
            with open('from.txt', 'a', encoding='utf-8') as f:
                f.write(email_address + '\n')
                f.flush()
                os.fsync(f.fileno())
            
            # Update counter
            with gui_instance.monitor_lock:
                gui_instance.fake_from_counter += 1
                counter_value = gui_instance.fake_from_counter
            
            # Update GUI
            gui_instance.root.after(0, lambda: gui_instance.fake_from_label.config(text=str(counter_value)))
            gui_instance.root.after(0, lambda: FileOperations.reload_from_addresses(gui_instance))
            
            print(f"{Fore.GREEN}[SAVE] Saved to from.txt | Counter: {counter_value}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}{'='*70}{Style.RESET_ALL}\n")
            
            gui_instance.monitor_log_print(f"💾 Saved to from.txt | Counter: {counter_value}", 'success')
            
            # Save config after each new email
            gui_instance.config_manager.save_config(gui_instance)
            
        except Exception as e:
            print(f"{Fore.RED}[ERROR] Failed saving to file: {e}{Style.RESET_ALL}")
            gui_instance.monitor_log_print(f"Error saving: {e}", 'error')
            
    @staticmethod
    def reload_from_addresses(gui_instance):
        """Reload from addresses from file - Filter out recipients"""
        try:
            if os.path.exists('from.txt'):
                with open('from.txt', 'r', encoding='utf-8') as f:
                    addresses = [line.strip() for line in f if line.strip()]
                    
                    # CRITICAL: Filter out recipients - Only keep FROM addresses
                    recipient_set = set(gui_instance.recipient_email_list) if hasattr(gui_instance, 'recipient_email_list') else set()
                    from_addresses_only = [addr for addr in addresses if addr and '@' in addr and addr not in recipient_set]
                    
                    # CLEAR and rebuild collected emails list - ONLY FROM addresses, NO recipients
                    gui_instance.collected_from_emails.clear()
                    gui_instance.collected_from_emails.extend(list(set(from_addresses_only)))  # Remove duplicates
                    
                    # Update the from addresses list
                    if hasattr(gui_instance, 'from_text'):
                        current_content = gui_instance.from_text.get(1.0, tk.END).strip()
                        if '\n'.join(addresses) != current_content:
                            gui_instance.from_text.delete(1.0, tk.END)
                            gui_instance.from_text.insert(1.0, '\n'.join(addresses))
                    
                    # Update stats if method exists
                    if hasattr(gui_instance, 'update_verification_stats'):
                        gui_instance.root.after(0, gui_instance.update_verification_stats)
                        
        except Exception as e:
            gui_instance.log_message(f"Error reloading from addresses: {e}", 'error')
    
    @staticmethod
    def refresh_collected_froms(gui_instance):
        """Refresh the verified and unverified textareas with counts - INSTANT UPDATES"""
        try:
            verified_count = len(gui_instance.verified_froms)
            unverified_count = len(gui_instance.unverified_froms)
            
            # Refresh verified textarea
            if hasattr(gui_instance, 'verified_from_text'):
                gui_instance.verified_from_text.delete(1.0, tk.END)
                for email in gui_instance.verified_froms:
                    gui_instance.verified_from_text.insert(tk.END, f"{email}\n")
            
            # Refresh unverified textarea
            if hasattr(gui_instance, 'unverified_from_text'):
                gui_instance.unverified_from_text.delete(1.0, tk.END)
                for email in gui_instance.unverified_froms:
                    gui_instance.unverified_from_text.insert(tk.END, f"{email}\n")
            
            # Update textarea labels with counts
            if hasattr(gui_instance, 'verified_label'):
                gui_instance.verified_label.config(text=f"✅ Verified ({verified_count})")
            if hasattr(gui_instance, 'unverified_label'):
                gui_instance.unverified_label.config(text=f"❌ Unverified ({unverified_count})")
                
            # Update bottom stats counter
            total = len(gui_instance.collected_from_emails)
            gui_instance.verify_stats_label.config(text=f"Collected: {total} | Verified: {verified_count} | Unverified: {unverified_count}")
        except Exception as e:
            print(f"{Fore.RED}Error refreshing collected froms: {e}{Style.RESET_ALL}")
    
    @staticmethod
    def save_verified_froms(gui_instance):
        """Save verified froms"""
        filename = filedialog.asksaveasfilename(title="Save Verified", defaultextension=".txt", filetypes=[("Text", "*.txt")])
        if filename:
            with open(filename, 'w') as f:
                f.write('\n'.join(gui_instance.verified_froms))
            messagebox.showinfo("Saved", f"Saved {len(gui_instance.verified_froms)} verified emails")
    
    @staticmethod
    def save_unverified_froms(gui_instance):
        """Save unverified froms"""
        filename = filedialog.asksaveasfilename(title="Save Unverified", defaultextension=".txt", filetypes=[("Text", "*.txt")])
        if filename:
            with open(filename, 'w') as f:
                f.write('\n'.join(gui_instance.unverified_froms))
            messagebox.showinfo("Saved", f"Saved {len(gui_instance.unverified_froms)} unverified emails")
    
    @staticmethod
    def load_verified_froms(gui_instance):
        """Load verified froms"""
        filename = filedialog.askopenfilename(title="Load Verified", filetypes=[("Text", "*.txt")])
        if filename:
            with open(filename, 'r') as f:
                gui_instance.verified_froms = [line.strip() for line in f if line.strip()]
            FileOperations.refresh_collected_froms(gui_instance)
            messagebox.showinfo("Loaded", f"Loaded {len(gui_instance.verified_froms)} verified emails")
    
    @staticmethod
    def load_unverified_froms(gui_instance):
        """Load unverified froms"""
        filename = filedialog.askopenfilename(title="Load Unverified", filetypes=[("Text", "*.txt")])
        if filename:
            with open(filename, 'r') as f:
                gui_instance.unverified_froms = [line.strip() for line in f if line.strip()]
            FileOperations.refresh_collected_froms(gui_instance)
            messagebox.showinfo("Loaded", f"Loaded {len(gui_instance.unverified_froms)} unverified emails")
    
    @staticmethod
    def save_verified_froms_to_file(gui_instance):
        """Save verified froms from textarea to file"""
        filename = filedialog.asksaveasfilename(title="Save Verified From Addresses", 
                                                defaultextension=".txt", 
                                                filetypes=[("Text", "*.txt")])
        if filename:
            try:
                content = gui_instance.verified_from_text.get(1.0, tk.END).strip()
                emails = [line.strip() for line in content.split('\n') if line.strip() and '@' in line]
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(emails))
                messagebox.showinfo("Saved", f"Saved {len(emails)} verified email addresses to {filename}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Error saving verified addresses: {e}")
    
    @staticmethod
    def load_verified_froms_from_file(gui_instance):
        """Load verified froms from file to textarea"""
        filename = filedialog.askopenfilename(title="Load Verified From Addresses", 
                                              filetypes=[("Text", "*.txt")])
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    emails = [line.strip() for line in f if line.strip() and '@' in line]
                
                # Update list and textarea
                gui_instance.verified_froms = emails
                gui_instance.verified_from_text.delete(1.0, tk.END)
                gui_instance.verified_from_text.insert(1.0, '\n'.join(emails))
                
                # Update stats
                FileOperations.refresh_collected_froms(gui_instance)
                messagebox.showinfo("Loaded", f"Loaded {len(emails)} verified email addresses")
            except Exception as e:
                messagebox.showerror("Load Error", f"Error loading verified addresses: {e}")
    
    @staticmethod
    def save_unverified_froms_to_file(gui_instance):
        """Save unverified froms from textarea to file"""
        filename = filedialog.asksaveasfilename(title="Save Unverified From Addresses", 
                                                defaultextension=".txt", 
                                                filetypes=[("Text", "*.txt")])
        if filename:
            try:
                content = gui_instance.unverified_from_text.get(1.0, tk.END).strip()
                emails = [line.strip() for line in content.split('\n') if line.strip() and '@' in line]
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(emails))
                messagebox.showinfo("Saved", f"Saved {len(emails)} unverified email addresses to {filename}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Error saving unverified addresses: {e}")
    
    @staticmethod
    def load_unverified_froms_from_file(gui_instance):
        """Load unverified froms from file to textarea"""
        filename = filedialog.askopenfilename(title="Load Unverified From Addresses", 
                                              filetypes=[("Text", "*.txt")])
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    emails = [line.strip() for line in f if line.strip() and '@' in line]
                
                # Update list and textarea
                gui_instance.unverified_froms = emails
                gui_instance.unverified_from_text.delete(1.0, tk.END)
                gui_instance.unverified_from_text.insert(1.0, '\n'.join(emails))
                
                # Update stats
                FileOperations.refresh_collected_froms(gui_instance)
                messagebox.showinfo("Loaded", f"Loaded {len(emails)} unverified email addresses")
            except Exception as e:
                messagebox.showerror("Load Error", f"Error loading unverified addresses: {e}")
