import markdown


toc = """
# Lockstep -- a Cross-Platform, Lightweight TCP-Based Synchronization System for Multiple Processes

I was thinking that I'd like to write programs like in Factorio.

In Factorio, one machine puts some kind of raw material onto a
conveyer belt, like from a box, and then other machines take things
off the conveyer belt, do something with them, and then put them
somewhere else.

Maybe put them into a box, or onto another conveyer belt, or into
another machine.  Just somewhere.

And I thought, "Man, I wish I could write programs like that."

[(Read more, in the introduction to Lockstep.)](doc_01_introduction.html)

----

Table of Contents:

- [Introduction](doc_01_introduction.html)
- [Protocol Documentation](doc_02_protocol.html)
- Unwritten: Installation
- Unwritten: Strategies (for coordinating programs in Lockstep)
"""

introduction = """

# Introduction to Lockstep - Make Your Programs Cooperate in Lockstep

I was thinking that I'd like to write programs like in Factorio.

[Factorio is a computer game.](https://www.factorio.com/)

![Title Screen for Factorio](http://%5B2601:601:a400:d20:a872:bf55:f1e:7dce%5D:8000/factorio_titleshot_2023-07-09.png)

In Factorio, one machine puts some kind of raw material onto a
conveyer belt, like from a box, and then other machines take things
off the conveyer belt, do something with them, and then put them
somewhere else.

![Machines and Conveyer Belts in Factorio](http://%5B2601:601:a400:d20:a872:bf55:f1e:7dce%5D:8000/factorio_screenshot_2023-07-09.png)

Maybe put them into a box, or onto another conveyer belt, or into
another machine.  Just somewhere.

And I thought, "Man, I wish I could write programs like that."

----

I mean, I can write individual programs that work like that, internally.

That's not too hard.

But when every program is individually assembled like this, where
you're building the infrastructure and the code and the machines
bespoke to each program, -- you're doing a lot of testing and
debugging work, over and over again.

It feels really inefficient.

----

A long time ago, I think maybe in the 1960's, there was UNIX.

And people in UNIX had the same idea.

(Who, in UNIX, had this great idea?

[It was Ken Thompson!](https://en.wikipedia.org/wiki/Ken_Thompson)  [Read more about the Unix Philosophy on Wikipedia.](https://en.wikipedia.org/wiki/Unix_philosophy))

In Unix, you construct commands like this:

    cat file.txt | grep "foo" | cut -d "," -f 2-5 | sort -r | uniq > file2.txt

There are so many things that are great about this!
* You don't have to write a whole new program, just to do what this does.
* It's very quick and easy to compose.
* It's also very easy to debug the process, because you can interrupt the flow at any point, and look at what's there.
* You don't have to debug the individual programs.  They're pretty bulletproof, having been reused time and time again.

The productivity gains are enormous!

----
"If UNIX is so great, then, why aren't you using it?"
Well, I do use tools like this on an ongoing basis.
But that's not the thing --
This works great for *commands*, but I want long-standing running continuous programs that coordinate like this.
*For example.*  Here's an assembly line:

| Step | Process | What Happens |
|--|--|--|
|1 | Google Chrome  & TCP Listener | The user clicks on the Google Chrome extension I wrote, and the current browser tab's Title and URL are emitted to a TCP listener process.  The TCP listener catches the Title and URL, and write them to a file, along with a timestamp. | 
| 2 | Bookmark Filer | The Title, URL, and Timestamp are read from the file.  Reading the timestamp, the Filer turns it into a YYYY-MM-DD, reads a file with YYYY-MM-DD.json, adds the bookmark to it, and then writes the updated YYYY-MM-DD.json file back out. |
| 3 | Recent Compiler | RECENT.json is updated to reflect the last N hours worth of bookmarks, from the YYYY-MM-DD.json files. |

You can see why a UNIX pipeline isn't a natural fit here.  It might be possible to make it work, but it's not quite set up right for this kind of thing.
* You could make the TCP listener the first part, and then it would output, when it received something, to the Bookmark filer.  I'd want to communicate by JSON.  But UNIX pipes communicate in a streaming way, not discretely.  The Bookmark Filer could get a partial bookmark, or it could get two bookmarks.  It's not really defined, as far as I know, how the bookmark filer would get JSON blobs.  So detecting blob boundaries is something I'd be concerned about.
* The "Recent" compiler isn't really part of a chain here, either -- it's not taking a direct output from the Bookmark Filer, to make it's file.  Rather, it just matters that it works *after* Bookmark Filer has done its work.  The only notice it's really looking for here, is something like: "Something happened and it's now time for me to do something."

So, this is the kind of problem that I'm interested in.

I'm interested in: How we can make assemblies out of little (small, trustworthy, easily understandable, and written in any number of programming languages) programs, that operate concurrently, and really work.  This is "Factorio programming."

----
And that turns out to be: kind of hard.

I've written little programs that do things like, "When a file appears in a certain spot, do something with it, and output the result in another spot."
But you know, it doesn't work out so great.
Here are two of the issues I've encountered:
* So, "output the result in another spot."  Sounds great.  But guess what?  You start writing the file to that spot, and the operating system puts a file there, and you're just starting to fill it out -- -- when the next program in the assembly line, says, "Oh, look!  A file!"  And it tries to read it, but you're not done yet.  But the target doesn't know that.  It just sees the new file in the space you were starting one.  It slurps up whatever it can, and then the whole thing is all 「おい、それめちゃくちゃやばいぜ」 as they would say in Japanese.  ("Meh-chaku-chah" 「滅茶苦茶」 is one of my favorite Japanese words, [and can be roughly translated as "FUBAR" in English.](https://chat.openai.com/share/24bea8bb-719b-480e-95fa-041f45195c27))
* Polling.  Polling!  Everything has to be constantly wound up in a tight little loop, asking the operating system, continuously, "Are we there yet?  Are we there yet?  Are we there yet?  Has somebody put a file there for me?  How about now?  How about now?  C'mon c'mon c'mon give me a file.  Is there a file there?  Is there?  How about now?"  It never stops!  And while having a couple processes irritating the fuck out of the operating system like this isn't much a problem, it doesn't exactly scale up very nicely.

To summarize:

| Problem | Description |
|--|--|
| File R/W Timing | There's no trivial way to see that the files are being read or written at the right times.  A file might be written, and not even read, before it's rewritten.  A file might be read in an incomplete state, even.  |
| Polling | The system relies on continuous polling, tying up system resources on a continuous basis.

----

I didn't want that to stop me, though.

Then I thought about something: "Everything in Factorio operates on a single clock."

Would it be possible to solve my problems, by introducing a shared clock?  So that all programs run within step windows?

"Yes and no," it turns out that the answer is.

There are still some issues I have found, -- and we'll talk about those another time.

But a shared continuous clock certainly makes this MUCH, MUCH easier.

Hence I wrote this code.  It's called: "**Lockstep.**"

Because it keeps everything moving along, ... ...*kind of* in lockstep.

I say "kind of" not because -- not because the software doesn't work, or anything like that.  Rather, because:  Just because things are running in the same uniform time boxes, it doesn't mean that they are running at exactly the same time within those uniform time boxes.  If the processes are a bunch of soldiers marching together in "lockstep", you can be sure that they have all touched the ground with the right foot, before any of them touch the ground with their left foot.  The system accurately guarantees that.  Perfectly.  But, ... do they all touch the ground with their left foot at the same exact moment?  Uh, definitely not.  Some will touch the left foot to the ground a bit before others do.  There are race conditions possible, within a single time cell.  But I get ahead of myself.

This is a good thing.  It's valuable.

And I think it should be easy for you to play with, easy for you to experiment with, if you are interested in this sort of thing.

----

In the future:

* How the protocol works.
* How to install and use lockstep.
* Strategies for putting multiple programs together in lockstep.

Note: I am very ADHD, and this is a hobby project, so "next time" may never, ever happen.

Lion -- 2023-07-09
"""

protocol = """

# Synchronous TCP Protocol Documentation

Lion Kimbro, 2023-07-09

## Overview

The Synchronous TCP Protocol enables synchronization between multiple processes. This documentation describes the message types exchanged between the server and client, including their byte representations and purposes.

## Messages

To mitigate processing complications, all messages are kept beneath a maximum TCP payload size of 536 bytes.  This choice is based on adhering to the minimum required IP datagram size of 576 bytes, accounting for the standard 20-byte TCP header and 20-byte IP header.  Utilizing smaller payload sizes helps minimize the likelihood of fragmentation and reassembly complexities that can arise when processing larger data frames.

Presently, the largest message size is 14 bytes.

Most messages are a single byte in length.

## Server to Client Messages

### 1. Protocol Version & Self-Identification

- Byte Representation: A
- Additional Details: The server sends 1 character representing the protocol version, followed by 12 bytes of self-identification.

### 2. "Go" Message

- Byte Representation: !
- Description: The server sends an individual "Go" message to each client, instructing them to proceed with their tasks concurrently. The "Go" message is followed by four bytes representing an integer (4 bytes, unsigned, little endian, integer) known as the "step count."

### 3. Refusal Messages

- Byte Representation: R
- Description: The server sends refusal messages to specific client processes, indicating that it will not work with those clients.

### 4. Server Exit Signal

- Byte Representation: X
- Description: The server sends a signal to indicate its exit or termination.

### 5. "Are you still there?" Signal

- Byte Representation: ?
- Description: The server can inquire if the client is still connected and active.

### 6. "I'm still here" Signal

- Byte Representation: .
- Description: The server responds to the client's "Are you still there?" signal, confirming its presence and active connection.

### 7. Broadcast Messages

- Byte Representation: T, S, E, C
- Description: The server can send broadcast messages to all client processes. Specific messages include:
  - (T) "This is taking longer than expected, please hang on..."
  - (S) "Shutting down in N seconds" (with 4 bytes unsigned integer countdown value)
  - (E) "Shutting down due to error"
  - (C) "Ceasing operation"

## Client to Server Messages

### 1. Protocol Version & Self-Identification

- Byte Representation: A
- Additional Details: The client sends 1 character representing the protocol version, followed by 12 bytes of self-identification.

### 2. Received Signal

- Byte Representation: K
- Description: The client sends a signal to indicate that it has received the "Go" message and is ready to proceed.

### 3. Done Signal

- Byte Representation: !
- Description: The client sends a signal to indicate the completion of its tasks.

### 4. Still Working Signal

- Byte Representation: W
- Description: The client can periodically send a signal to inform the server that it is still actively working on its tasks.

### 5. I Am Here But Not Working Message

- Byte Representation: .
- Description: The client sends a signal to indicate that it is still connected but not actively working.

### 6. Are You Still There? Message

- Byte Representation: ?
- Description: The client can inquire if the server is still connected and active.

### 7. Client Exit Signal

- Byte Representation: X
- Description: The client sends a signal to indicate its exit or termination.

----

## "The Least You Could Do"

- As a client, establish a TCP connection to the server.
- Send the server a packet that reads b"A1mynameisjohn".  The name, after b"A1", can be anything made of ASCII printable characters, but it MUST be 12 characters long.  It can include spaces.
- You can ignore the server's message to you, telling you its own name.  That message will start with b"A1" as well.
- Wait until you get a b"!" from the server.  That's the GO signal!  But don't go just yet!  Read the next four bytes, and interpret them as an unsigned integer.  That's called the "step count."  The server might be configured to deliver the numbers 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, ... or any other monotonically increasing, and then resetting back to 0, -- count.  It could climb up to MAXINT.  Whatever.  But it's there so that programs can orient their timing with respect to one another.
   - In Python, you can decode this with struct.unpack("<I", data)[0]
- Acknowledge receipt.  Reply with b"K".
- Do your task.
- When you're done, or at least when you reach a breaking point that is consistent with system promises, respond with b"!".
- Then wait until you receive b"!" from the server.  That's the next round.
- Ignore anything else that isn't in the above.

That's all you have to do.  You can quit suddenly, and the server will be fine, no hard feelings.

There is protocol support for answering requests from a confused server -- it might send you b"?" meaning, "Hey, ...  Are you there? ... Haven't heard from you in a while."  In which case you could respond with b"W" ("still working!") or b"." ("I'm here, but I'm not really doing anything.")

But that's not really required.  You could totally just blow off the server, and do what you're doing.  Now, if the server gets impatient, it might cut your process out of consideration.  So you might want to respond in time.

But these are more edge cases for the time being.  I'm just interested in getting you started at this point.

I'm interested in telling you here, the least you could do, to get something going.  And honestly, that'll work for the great majority of cases, I think.
"""

def make(src, filename):
    html = markdown.markdown(src, extensions=["tables"])
    open(filename, "w", encoding="utf-8").write(html)

make(toc, "index.html")
make(introduction, "doc_01_introduction.html")
make(protocol, "doc_02_protocol.html")

