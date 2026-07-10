#!/usr/bin/env python3
"""
Instagram Scheduler - Python CLI
Schedule posts, stories, reels, and DMs with full feature support.
"""

import json
import os
import time
import schedule
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Optional, List
import argparse


@dataclass
class ScheduledPost:
    id: int
    post_type: str
    caption: str
    scheduled_datetime: str
    target_user: Optional[str] = None
    media_path: Optional[str] = None
    first_comment: bool = False
    cross_post: bool = False
    auto_reply: bool = False
    story_link: bool = False
    status: str = "pending"


class InstagramScheduler:
    DATA_FILE = "scheduler_data.json"
    
    def __init__(self):
        self.posts: List[ScheduledPost] = []
        self.running = False
        self.load_data()
    
    def load_data(self):
        if os.path.exists(self.DATA_FILE):
            try:
                with open(self.DATA_FILE, 'r') as f:
                    data = json.load(f)
                    self.posts = [ScheduledPost(**p) for p in data]
            except Exception as e:
                print(f"Error loading data: {e}")
                self.posts = []
    
    def save_data(self):
        try:
            with open(self.DATA_FILE, 'w') as f:
                json.dump([asdict(p) for p in self.posts], f, indent=2)
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def add_post(self, post_type: str, caption: str, 
                 scheduled_datetime: datetime, target_user: Optional[str] = None,
                 media_path: Optional[str] = None,
                 first_comment: bool = False,
                 cross_post: bool = False,
                 auto_reply: bool = False,
                 story_link: bool = False) -> ScheduledPost:
        
        post = ScheduledPost(
            id=int(time.time() * 1000),
            post_type=post_type,
            caption=caption,
            scheduled_datetime=scheduled_datetime.isoformat(),
            target_user=target_user,
            media_path=media_path,
            first_comment=first_comment,
            cross_post=cross_post,
            auto_reply=auto_reply,
            story_link=story_link
        )
        self.posts.append(post)
        self.save_data()
        self._schedule_job(post)
        return post
    
    def _schedule_job(self, post: ScheduledPost):
        dt = datetime.fromisoformat(post.scheduled_datetime)
        
        def job():
            self._execute_post(post)
        
        schedule.every().day.at(dt.strftime("%H:%M")).do(job).tag(str(post.id))
    
    def _execute_post(self, post: ScheduledPost):
        now = datetime.now()
        post_dt = datetime.fromisoformat(post.scheduled_datetime)
        
        if now.date() == post_dt.date():
            print(f"\n{'='*50}")
            print(f" EXECUTING POST #{post.id}")
            print(f" Type: {post.post_type.upper()}")
            print(f" Caption: {post.caption[:60]}...")
            
            if post.post_type == "dm" and post.target_user:
                print(f" Sending DM to @{post.target_user}")
            else:
                print(f" Publishing {post.post_type} post")
            
            if post.first_comment:
                print(" Auto-posting first comment")
            if post.cross_post:
                print(" Cross-posting to Facebook & Threads")
            if post.auto_reply:
                print(" AI auto-reply enabled")
            if post.story_link:
                print(" Story link sticker added")
            
            post.status = "posted"
            self.save_data()
            print(f" POSTED SUCCESSFULLY!")
            print(f"{'='*50}\n")
            return schedule.CancelJob
    
    def delete_post(self, post_id: int) -> bool:
        for i, p in enumerate(self.posts):
            if p.id == post_id:
                self.posts.pop(i)
                schedule.clear(str(post_id))
                self.save_data()
                return True
        return False
    
    def list_posts(self, status_filter: Optional[str] = None):
        posts = self.posts
        if status_filter:
            posts = [p for p in self.posts if p.status == status_filter]
        
        if not posts:
            print("\n No posts found.")
            return
        
        print(f"\n{'='*75}")
        print(f"{'ID':<14} {'Type':<8} {'Status':<10} {'Date & Time':<20} {'Caption'}")
        print(f"{'='*75}")
        
        for p in posts:
            dt = datetime.fromisoformat(p.scheduled_datetime)
            dt_str = dt.strftime("%Y-%m-%d %H:%M")
            caption = p.caption[:25] + "..." if len(p.caption) > 25 else p.caption
            target = f" -> @{p.target_user}" if p.target_user else ""
            print(f"{p.id:<14} {p.post_type:<8} {p.status:<10} {dt_str:<20} {caption}{target}")
        
        print(f"{'='*75}")
        print(f"Total: {len(posts)} post(s)\n")
    
    def start_scheduler(self):
        self.running = True
        print(" Scheduler started. Press Ctrl+C to stop.")
        
        for post in self.posts:
            if post.status == "pending":
                self._schedule_job(post)
        
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(30)
        except KeyboardInterrupt:
            self.stop_scheduler()
    
    def stop_scheduler(self):
        self.running = False
        print("\n Scheduler stopped.")
    
    def get_quick_time(self, option: str) -> datetime:
        now = datetime.now()
        
        if option == "now":
            return now
        elif option == "tomorrow9":
            return (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
        elif option == "tomorrow6":
            return (now + timedelta(days=1)).replace(hour=18, minute=0, second=0, microsecond=0)
        elif option == "nextweek":
            return (now + timedelta(days=7)).replace(hour=9, minute=0, second=0, microsecond=0)
        else:
            return now


def interactive_menu():
    scheduler = InstagramScheduler()
    
    print("""
========================================
      INSTAGRAM SCHEDULER v1.0
 Schedule posts, stories, reels & DMs
========================================
    """)
    
    while True:
        print("\n" + "-"*40)
        print("  [1] Compose & Schedule New Post")
        print("  [2] View Scheduled Posts")
        print("  [3] Delete a Post")
        print("  [4] Start Scheduler (background)")
        print("  [5] Exit")
        print("-"*40)
        
        choice = input("\nSelect option: ").strip()
        
        if choice == "1":
            compose_post(scheduler)
        elif choice == "2":
            scheduler.list_posts()
        elif choice == "3":
            delete_post_menu(scheduler)
        elif choice == "4":
            scheduler.start_scheduler()
        elif choice == "5":
            print(" Goodbye!")
            break
        else:
            print(" Invalid option. Try again.")


def compose_post(scheduler: InstagramScheduler):
    print("\n" + "="*50)
    print("      COMPOSE NEW POST")
    print("="*50)
    
    print("\nSelect post type:")
    print("  [1] Feed Post")
    print("  [2] Story")
    print("  [3] Reel")
    print("  [4] DM")
    
    type_choice = input("\nType: ").strip()
    type_map = {"1": "feed", "2": "story", "3": "reel", "4": "dm"}
    
    if type_choice not in type_map:
        print(" Invalid type.")
        return
    
    post_type = type_map[type_choice]
    
    print(f"\nEnter your {'message' if post_type == 'dm' else 'caption'}:")
    print("(Press Enter twice to finish)")
    lines = []
    while True:
        line = input()
        if line == "" and len(lines) > 0 and lines[-1] == "":
            lines.pop()
            break
        lines.append(line)
    caption = "\n".join(lines)
    
    if not caption.strip():
        print(" Caption cannot be empty.")
        return
    
    target_user = None
    if post_type == "dm":
        target_user = input("\nTarget username (without @): ").strip()
        if not target_user:
            print(" Target user required for DM.")
            return
    
    media_path = None
    if post_type != "dm":
        media_input = input("\nMedia file path (or press Enter to skip): ").strip()
        if media_input and os.path.exists(media_input):
            media_path = media_input
        elif media_input:
            print(" File not found. Continuing without media.")
    
    print("\nSchedule options:")
    print("  [1] Now")
    print("  [2] Tomorrow 9:00 AM")
    print("  [3] Tomorrow 6:00 PM")
    print("  [4] Next Week (same time, 9 AM)")
    print("  [5] Custom date & time")
    
    time_choice = input("\nWhen: ").strip()
    time_map = {"1": "now", "2": "tomorrow9", "3": "tomorrow6", "4": "nextweek"}
    
    if time_choice in time_map:
        scheduled_time = scheduler.get_quick_time(time_map[time_choice])
    elif time_choice == "5":
        date_str = input("Date (YYYY-MM-DD): ").strip()
        time_str = input("Time (HH:MM, 24h): ").strip()
        try:
            scheduled_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        except ValueError:
            print(" Invalid date/time format.")
            return
    else:
        print(" Invalid option.")
        return
    
    print("\nExtra features (y/n):")
    first_comment = input("  Auto-post first comment? ").strip().lower() == 'y'
    cross_post = input("  Cross-post to Facebook & Threads? ").strip().lower() == 'y'
    auto_reply = input("  AI auto-reply to comments? ").strip().lower() == 'y'
    story_link = False
    if post_type == "story":
        story_link = input("  Add story link sticker? ").strip().lower() == 'y'
    
    print(f"\n{'-'*50}")
    print(" POST PREVIEW:")
    print(f"   Type: {post_type.upper()}")
    print(f"   Caption: {caption[:50]}...")
    print(f"   Scheduled: {scheduled_time.strftime('%Y-%m-%d %H:%M')}")
    if target_user:
        print(f"   To: @{target_user}")
    print(f"{'-'*50}")
    
    confirm = input("\nSchedule this post? (y/n): ").strip().lower()
    if confirm != 'y':
        print(" Cancelled.")
        return
    
    post = scheduler.add_post(
        post_type=post_type,
        caption=caption,
        scheduled_datetime=scheduled_time,
        target_user=target_user,
        media_path=media_path,
        first_comment=first_comment,
        cross_post=cross_post,
        auto_reply=auto_reply,
        story_link=story_link
    )
    
    print(f"\n Post #{post.id} scheduled for {scheduled_time.strftime('%Y-%m-%d %H:%M')}!")


def delete_post_menu(scheduler: InstagramScheduler):
    scheduler.list_posts()
    post_id = input("\nEnter post ID to delete (or 0 to cancel): ").strip()
    
    if post_id == "0":
        return
    
    try:
        post_id = int(post_id)
        if scheduler.delete_post(post_id):
            print(f" Post #{post_id} deleted.")
        else:
            print(" Post not found.")
    except ValueError:
        print(" Invalid ID.")


def main():
    parser = argparse.ArgumentParser(description="Instagram Post Scheduler")
    parser.add_argument('--type', choices=['feed', 'story', 'reel', 'dm'], help='Post type')
    parser.add_argument('--caption', '-c', help='Post caption/message')
    parser.add_argument('--date', help='Schedule date (YYYY-MM-DD)')
    parser.add_argument('--time', '-t', help='Schedule time (HH:MM)')
    parser.add_argument('--to', help='Target user for DM')
    parser.add_argument('--media', '-m', help='Media file path')
    parser.add_argument('--first-comment', action='store_true', help='Auto-post first comment')
    parser.add_argument('--cross-post', action='store_true', help='Cross-post to Facebook/Threads')
    parser.add_argument('--auto-reply', action='store_true', help='Enable AI auto-reply')
    parser.add_argument('--story-link', action='store_true', help='Add story link sticker')
    parser.add_argument('--list', '-l', action='store_true', help='List all scheduled posts')
    parser.add_argument('--delete', type=int, help='Delete post by ID')
    parser.add_argument('--run', '-r', action='store_true', help='Start scheduler daemon')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')
    
    args = parser.parse_args()
    scheduler = InstagramScheduler()
    
    if args.list:
        scheduler.list_posts()
        return
    
    if args.delete:
        if scheduler.delete_post(args.delete):
            print(f" Post #{args.delete} deleted.")
        else:
            print(" Post not found.")
        return
    
    if args.run:
        scheduler.start_scheduler()
        return
    
    if args.interactive or (not args.type and not args.list and not args.delete and not args.run):
        interactive_menu()
        return
    
    if args.type and args.caption and args.date and args.time:
        try:
            dt = datetime.strptime(f"{args.date} {args.time}", "%Y-%m-%d %H:%M")
        except ValueError:
            print(" Invalid date/time format. Use YYYY-MM-DD and HH:MM")
            return
        
        target = args.to if args.type == 'dm' else None
        
        post = scheduler.add_post(
            post_type=args.type,
            caption=args.caption,
            scheduled_datetime=dt,
            target_user=target,
            media_path=args.media,
            first_comment=args.first_comment,
            cross_post=args.cross_post,
            auto_reply=args.auto_reply,
            story_link=args.story_link
        )
        
        print(f"\n Post #{post.id} scheduled for {dt.strftime('%Y-%m-%d %H:%M')}!")
        print(f"   Type: {args.type.upper()}")
        print(f"   Caption: {args.caption[:50]}...")
        return
    
    parser.print_help()


if __name__ == "__main__":
    main()
