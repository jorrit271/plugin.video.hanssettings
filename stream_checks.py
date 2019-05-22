import requests, queue, threading, sys, subprocess

from resources.lib.hanssettings import HansSettings
from streamcheck.lib.streamobject import StreamObject
from streamcheck.lib.checks.ffprobecheck import FFProbeCheck
from streamcheck.lib.checks.statuscodecheck import StatusCodeCheck
from streamcheck.lib.checks.m3u8redirector302 import M3u8RedirectOr302

_hanssettings = HansSettings()
# hier kan je proberen hoeveel threads / workers je tegelijk aan hebt.
_num_worker_threads = 50
_timeout = 5

print(_hanssettings)

# we draaien #num_worker_threads van deze workers welke de queue leeg halen (tot None)
def worker():
    while True:
        stream = _q.get()
        if stream is None:
            break
        # We proberen een http status-code te bepalen
        try:
            StatusCodeCheck(stream, _timeout).run()
        except requests.ConnectionError:            
            print("Failed to connect - StatusCodeCheck - " + stream.stream_label)
        except:
            print("Error - StatusCodeCheck - " + stream.stream_label)            
        # kijken of de stream wat oplevert met FFProbe
        try:
            #print('in: ' + stream.stream_url + ' ('+str(stream.id)+') ')
            FFProbeCheck(stream, _timeout).run()
            #print('out: ' + stream.stream_url + ' ('+str(stream.id)+') ' + stream.status)
        except subprocess.TimeoutExpired:
            print("Timeout - FFProbeCheck - " + stream.stream_label)
        except:
            print("Error - FFProbeCheck - " + stream.stream_label)
        # redirect goed zetten
        try:
            #print('in: ' + stream.stream_url + ' ('+str(stream.id)+') ')
            M3u8RedirectOr302(stream, _timeout).run()
            #print('out: ' + stream.stream_url + ' ('+str(stream.id)+') ' + stream.status)
        except requests.ConnectionError:            
            print("Failed to connect - M3u8RedirectOr302 - " + stream.stream_label)            
        except:
            print("Error - M3u8RedirectOr302 - " + stream.stream_label)
        # kijken of de new url stream wat oplevert met FFProbe
        try:
            #print('in: ' + stream.stream_url + ' ('+str(stream.id)+') ')
            FFProbeCheck(stream, _timeout).run_new()
            #print('out: ' + stream.stream_url + ' ('+str(stream.id)+') ' + stream.status)
        except subprocess.TimeoutExpired:
            print("Timeout - FFProbeCheck - " + stream.stream_label)
        except:
            print("Error - FFProbeCheck - " + stream.stream_label)            
        # we zijn klaar met deze queue opdracht
        _q.task_done()

def loop():
    # we maken alvast wat workers welke wachten op vulling van de queue
    # https://docs.python.org/3/library/queue.html
    threads = []
    for i in range(_num_worker_threads):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)

    # we hebben nu alle streams en gaan ze op een queue zetten
    for stream in [st for st in all_streams if st.status != 'OK']:
        _q.put(stream)

    # block until all tasks are done
    _q.join()

    # stop alle workers
    for i in range(_num_worker_threads):
        _q.put(None)
    for t in threads:
        t.join()

#print(h.get_overzicht(h.get_dataoverzicht()))
print('\n\n')
content_type = 'tv'

# ophalen alle bestandsnamen welke we kunnen ophalen in github.
stream_list_github = _hanssettings.get_data_from_github_file_bouquets(content_type)
github_stream_filenames = _hanssettings.get_stream_files_from_bouguet(stream_list_github, content_type)

# totaal aantal streambestanden welke zijn op te halen van github.
count_stream_filenames = len(github_stream_filenames)

print('totaal github-files: ' + str(count_stream_filenames))

# we gaan alle streams per github-file toevoegen aan 1 grote lijst.
all_streams = list()
i = 0 # file teller
j = 0 # stream teller
for filename in github_stream_filenames:
    i = i + 1
    datafile = _hanssettings.get_data_from_github_file(filename)
    name = _hanssettings.get_name(datafile, filename)
    print(str(i) + ': ' + name)
    streams_datafile = _hanssettings.get_streams(datafile)
    for stream in streams_datafile:
        j = j + 1
        all_streams.append(StreamObject(j, filename, name, stream['label'], stream['url'], stream['header']))
    # voor testen even met 4 files
    if (i == 4):
        break

sum_run0 = sum(st.status != 'OK' for st in all_streams)
print('Run0:' + str(sum_run0))
print('---')

_q = queue.Queue()
loop()
sum_run1 = sum(st.status != 'OK' for st in all_streams)
print('Run1:' + str(sum_run1))
print('---')

_q = queue.Queue()
_timeout = 10
loop()
sum_run2 = sum(st.status != 'OK' for st in all_streams)
print('Run2:' + str(sum_run2))
print('---')

_q = queue.Queue()
_timeout = 30
loop()
sum_run3 = sum(st.status != 'OK' for st in all_streams)
print('Run3:' + str(sum_run3))
print('---')

print('done queues')
for stream in all_streams:
    # laat alle vreemde eenden zien, welke nu nog niet wilde
    if (stream.status != 'OK' != 200):
        print('---')
        print(stream.bouquet_name)
        print(stream.stream_label)
        print(stream.stream_url)
        print(stream.stream_header)
        print(stream.httpstatuscode)
        print('---')
print('---')
print('Run0')
print(sum_run0)
print('---')
print('Run1')
print(sum_run1)
print('---')
print('Run2')
print(sum_run2)
print('---')
print('Run3')
print(sum_run3)
print('---')