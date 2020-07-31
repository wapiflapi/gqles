import React, { useState, useMemo } from 'react';

import { ApolloClient, ApolloProvider, InMemoryCache, useQuery } from '@apollo/client';
import { ApolloLink } from 'apollo-link';
import { RetryLink } from 'apollo-link-retry';
import { HttpLink } from 'apollo-link-http';

import { loader } from 'graphql.macro';

import { withStyles } from '@material-ui/core/styles';
import { green, pink } from '@material-ui/core/colors';

import Accordion from '@material-ui/core/Accordion';
import AccordionDetails from '@material-ui/core/AccordionDetails';
import AccordionSummary from '@material-ui/core/AccordionSummary';
import AccordionActions from '@material-ui/core/AccordionActions';
import ArrowDownwardIcon from '@material-ui/icons/ArrowDownward';
import ArrowForwardIcon from '@material-ui/icons/ArrowForward';
import ArrowUpwardIcon from '@material-ui/icons/ArrowUpward';
import Avatar from '@material-ui/core/Avatar';
import Button from '@material-ui/core/Button';
import Box from '@material-ui/core/Box';
import Card from '@material-ui/core/Card';
import CardHeader from '@material-ui/core/CardHeader';
import ChevronLeftIcon from '@material-ui/icons/ChevronLeft';
import ClickAwayListener from '@material-ui/core/ClickAwayListener';
import Container from '@material-ui/core/Container';
import Divider from '@material-ui/core/Divider';
import ExpandMoreIcon from '@material-ui/icons/ExpandMore';
import Grid from '@material-ui/core/Grid';
import HourglassEmptyIcon from '@material-ui/icons/HourglassEmpty';
import IconButton from '@material-ui/core/IconButton';
import Link from '@material-ui/core/Link';
import List from '@material-ui/core/List';
import ListItem from '@material-ui/core/ListItem';
import ListItemAvatar from '@material-ui/core/ListItemAvatar';
import ListItemSecondaryAction from '@material-ui/core/ListItemSecondaryAction';
import ListItemText from '@material-ui/core/ListItemText';
import ListSubheader from '@material-ui/core/ListSubheader';
import NavigateNextIcon from '@material-ui/icons/NavigateNext';
import Paper from '@material-ui/core/Paper';
import SearchIcon from '@material-ui/icons/Search';
import Skeleton from '@material-ui/lab/Skeleton';
import SvgIcon from '@material-ui/core/SvgIcon';
import Typography from '@material-ui/core/Typography';
import UnfoldMoreIcon from '@material-ui/icons/UnfoldMore';

import {
    // TODO: This should not be used in production.
    // https://github.com/mui-org/material-ui/issues/13394
    unstable_createMuiStrictModeTheme as createMuiTheme,
} from '@material-ui/core/styles';

import { Router, Link as RouterLink, useMatch, Redirect } from "@reach/router";

import copy from 'clipboard-copy';
import TimeAgo from 'react-timeago';

import DelayedRender from './DelayedRender';
import JSONView, { loadB64JSONOrNothing } from './JSONTree.js';


const client = new ApolloClient({
    cache: new InMemoryCache(),
    link: ApolloLink.from([
        new RetryLink(),
        new HttpLink({ uri: 'http://localhost:8000/graphql/' })
    ]),
});


const GetNotificationsQuery = loader(
    './GetNotifications.graphql');

const GetEventLogQuery = loader(
    './GetEventLog.graphql');



function FriendlyTimeAgo({ date }) {
    const [friendly, setFriendly] = useState(true);

    return (date === undefined ? (
        <Skeleton width="7em" />
    ) : friendly ? (
        <Link
          color="inherit"
          fontSize="inherit"
          onClick={() => setFriendly(!friendly)}
        >
          <TimeAgo date={date} />
        </Link>

    ) : (
        <ClickAwayListener onClickAway={() => setFriendly(!friendly)}>
          <Box component="span" fontFamily="Monospace">
            {date}
          </Box>
        </ClickAwayListener>
    ));
}




function FriendlyList({children, empty, ...props}) {
    return (
        !Array.isArray(children) || children.length ?
            <List {...props}>
              {children}
            </List>
        : <DelayedRender>
            <Box m={4}>
              {empty ||
               <Grid spacing={2} container direction="row" alignItems="center" justify="center">
                 <Grid item container xs={12} justify="center">
                   <SearchIcon fontSize="large" />
                 </Grid>
                 <Grid item>
                   There is nothing here.
                 </Grid>
               </Grid>
              }
            </Box>
          </DelayedRender>
    );
}

function EventTopic({ event }) {
    return (event ? (
        <Box component="span" fontFamily="Monospace">
          {event.topic.split("#").map((sub, i) => (i === 0 ? (
              <small key={i} style={{display: "inline-block"}}>
                {sub}
              </small>

          ) : (
              <span key={i} style={{display: "inline-block"}}>
                {`#${sub}`}
              </span>
          )
          ))}
        </Box>
    ) : (
        <Skeleton width="25em"/>
    ));
}

function EventLink({ event }) {

    if (event === undefined || event.id === undefined) {
        return <Skeleton width="25em"/>;
    }

    const fullpath = `/event/${event.id}`;

    return (
        <span style={{
            display: 'flex',
            alignItems: 'center'
        }}>
          <IconButton
            aria-label="clipboard"
            size="small"
            onClick={() => copy(event.id)}
          >
            <SvgIcon fontSize="inherit">
              <path d="M19 2h-4.18C14.4.84 13.3 0 12 0c-1.3 0-2.4.84-2.82 2H5c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-7 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm7 18H5V4h2v3h10V4h2v16z"/>
            </SvgIcon>
          </IconButton>
          <Box component="span" fontFamily="Monospace">
            <Link
              component={RouterLink}
              to={fullpath}
            >
              {event.id}
            </Link>
          </Box>
        </span>
    );
}

function EventListItem({ event, avatar }) {

    const match = useMatch(event && event.id || 'this-does-not-exist');

    return (
        <ListItem alignItems="flex-start" selected={!!match} >
          {(event === undefined || avatar) && (
              <ListItemAvatar>{event ? (
                  avatar
              ) : <Skeleton variant="circle" width={40} height={40} />}
              </ListItemAvatar>
          )}
          <ListItemText
            primary={<EventTopic event={event} />}
            secondary={
                <>
                  <EventLink event={event} />
                  <FriendlyTimeAgo date={event && event.timestamp} />
                </>
            }
          />
          {event && (
              <ListItemSecondaryAction>
                <IconButton
                  edge="end"
                  aria-label="more"
                  component={RouterLink}
                  to={event.id}
                >
                  <NavigateNextIcon />
                </IconButton>
              </ListItemSecondaryAction>
          )}
        </ListItem>

    );
}

const FixedAccordionSummary = withStyles({
    content: {
        minWidth: 0,
    },
})(AccordionSummary);

function AutoSelectCode({ children, ...props }) {
    return (
        <Typography noWrap {...props}>
          <Box
            component="span"
            fontFamily="Monospace"
            style={{
                userSelect: "all",
            }}
            onClick={(event) => event.stopPropagation()}
            onFocus={(event) => event.stopPropagation()}
          >
            {children}
          </Box>
        </Typography>

    );
}

function StateInsight({
    stateInsight
}) {

    return (stateInsight ? stateInsight.filter(stateInsight => ![
        "timestamp",
        "originator_id",
        "originator_version",
        "originator_topic",
    ].includes(stateInsight.key)).map(((stateInsight, i) => (
        <Accordion key={i} elevation={0}>
          <FixedAccordionSummary
            style={{minWidth: 0}}
            expandIcon={<ExpandMoreIcon />}
            style={{userSelect: 'text'}}
          >
            <Grid container my={2} spacing={2}>
              {/* We're disabling click & focus on the fields, */}
              {/* we want to provide easy selection of keys & values. */}

              <Grid item xs={4} >
                <AutoSelectCode noWrap>
                  {stateInsight.key}
                </AutoSelectCode>
              </Grid>

              <Grid item xs={8}>
                <AutoSelectCode noWrap color="textSecondary">
                  {stateInsight.text}
                </AutoSelectCode>
              </Grid>

            </Grid>

          </FixedAccordionSummary>

          <AccordionDetails>
            <JSONView
              data={{[stateInsight.key]: (
                  // FIXME: We should catch errors from JSON.parse!
                  stateInsight.json ? JSON.parse(stateInsight.json)
                      : stateInsight.text
              )}}
              hideRoot={true}
              sortObjectKeys={true}
              shouldExpandNode={(keyName, data, level) => level < 2}
            />
          </AccordionDetails>
        </Accordion>
    ))) : stateInsight === null ? (
        // TODO: better message.
        <span>Failed to load state insight.</span>
    ) : stateInsight === undefined ? (
        <Box m={2}>
          <Grid container my={2} spacing={2}>
            <Grid item xs={4} >
              <Skeleton width="5em"/>
            </Grid>
            <Grid item xs={8}>
              <Skeleton width="15em"/>
            </Grid>
          </Grid>
        </Box>
    ) : undefined);

}

function EventWithContext({
    event,
    avatar
}) {

    // TODO: In some cases we already have partial data in cache before
    // we fire the request. Take that into account.

    return (
        <Card>

          <CardHeader
            avatar={avatar}
            title={<EventTopic event={event} />}
            subheader={
                <>
                  <EventLink event={event} />
                  <FriendlyTimeAgo date={event && event.timestamp} />
                </>
            }
          />

          <StateInsight stateInsight={event && event.stateInsight} />

        </Card>
    );

}


function HasMoreListSubheader({
    more
}) {
    return (
        <ListSubheader>
          <Button
            variant="text"
            color="primary"
            startIcon={<UnfoldMoreIcon />}
          >
            load {more || "more"}
          </Button>
        </ListSubheader>
    );
}

function EventLogSection({
    events,
    hasMoreTop,
    loadMoreTop,
    hasMoreBottom,
    loadMoreBottom,
    more,
    avatar,
}) {

    // TODO: We should be using react-window for virtualized lists.
    // https://material-ui.com/components/lists/#virtualized-list

    return (
        <List>
          {hasMoreTop && (
              <HasMoreListSubheader more={more} />
          )}
          {events !== undefined ? events.length ? events.map((event, i) => (
              // State 1: We have events to display!
              <EventListItem
                key={event ? event.id : i} // In case they're not loaded yet.
                event={event}
                avatar={avatar}
              />
          )).reverse() : (
              // State 2: We know there are no events.
              <ListItem>
                <ListItemAvatar>
                  <Avatar>
                    <HourglassEmptyIcon />
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={more ? `There are no ${more} for now.` : "Nothing here for now."}
                  secondary="We will reload this for you when content becomes available."
                />
              </ListItem>
          ) : <DelayedRender>{[1, 2, 3].map((key) => (
              // State 3: We don't know if there will be any events.
              <EventListItem key={key} />
          ))}</DelayedRender>}
          {hasMoreBottom && (
              <HasMoreListSubheader more={more} />
          )}
        </List>
    );
}

const PrimaryAvatar = withStyles((theme) => ({
    root: {
        color: theme.palette.primary.contrastText,
        backgroundColor: theme.palette.primary.main,
    },
}))(Avatar);

const SecondaryAvatar = withStyles((theme) => ({
    root: {
        color: theme.palette.secondary.contrastText,
        backgroundColor: theme.palette.secondary.main,
    },
}))(Avatar);

function EventLog({
    currentEvent,
    previousEvents,
    previousEventsHasMoreTop,
    previousEventsHasMoreBottom,
    nextEvents,
    nextEventsHasMoreTop,
    nextEventsHasMoreBottom,
    // Load more previous, and load more next go here.
    // Also pass hasMore for both.
}) {

    return (
        <>
          {(nextEvents !== null && (
              <EventLogSection
                events={nextEvents}
                hasMoreTop={nextEventsHasMoreTop}
                hasMoreBottom={nextEventsHasMoreBottom}
                avatar={<PrimaryAvatar><ArrowUpwardIcon/></PrimaryAvatar>}
                more="later events"
              />
          ))}
          {(currentEvent !== null && (
              <EventLogSection
                events={[currentEvent]}
                avatar={<SecondaryAvatar><ArrowForwardIcon/></SecondaryAvatar>}
              />
          ))}
          {(previousEvents !== null && (
              <EventLogSection
                events={previousEvents}
                hasMoreTop={previousEventsHasMoreTop}
                hasMoreBottom={previousEventsHasMoreBottom}
                avatar={<PrimaryAvatar><ArrowDownwardIcon/></PrimaryAvatar>}
                more="earlier events"
              />
          ))}
        </>
    );

}


function LogViewer({
    currentEvent,
    previousEvents,
    previousEventsHasMoreTop,
    previousEventsHasMoreBottom,
    nextEvents,
    nextEventsHasMoreTop,
    nextEventsHasMoreBottom,
    // Load more previous, and load more next go here.
    // Also pass hasMore for both.
}) {

    // This handles both eventlog and notificationlog

    // This also handles state regarding:
    // - preview hashes.

    const match = useMatch(":applicationName/:originatorId/:originatorVersionString");

    const previewEvent = useMemo(() => [
        currentEvent, ...(previousEvents || []), ...(nextEvents || []),
    ].find((event) => (
        match && event &&
            match.applicationName === event.applicationName &&
            match.originatorId === event.originatorId &&
            parseInt(match.originatorVersionString, 10) === event.originatorVersion
    )) || currentEvent, [match, currentEvent, previousEvents, nextEvents]);

    return (
        <Grid container spacing={2}>
          <Grid item xs={12} md={6} >
            <EventLog
              currentEvent={currentEvent}
              previousEvents={previousEvents}
              nextEvents={nextEvents}
              previousEventsHasMoreTop={previousEventsHasMoreTop}
              previousEventsHasMoreBottom={previousEventsHasMoreBottom}
              nextEventsHasMoreTop={nextEventsHasMoreTop}
              nextEventsHasMoreBottom={nextEventsHasMoreBottom}
            />
          </Grid>
          <Grid item xs={12} md={6} >
            {previewEvent !== null ? (
                <EventWithContext
                event={previewEvent}
                />
            ) : (
                // It's okay if this looks empty, but we could add a splash!
                undefined
            )}
          </Grid>
        </Grid>
    );
}

function EventLogRouteComponent({
    applicationName, originatorId, originatorVersionString
}) {

    const { error, data, loading } = useQuery(GetEventLogQuery, {
        pollInterval: 5000,
        variables: {
            applicationName,
            originatorId,
            originatorVersion: parseInt(originatorVersionString, 10),
        }
    });

    const match = useMatch(":applicationName/:originatorId/:originatorVersionString");

    if (!match) {
        return (
            <Redirect
              noThrow
              from="/"
              to={`${applicationName}/${originatorId}/${originatorVersionString}`}
            />
        );
    }

    return (
        <LogViewer
          currentEvent={data && data.event}
          previousEvents={data && data.event && (
              data.event.previousEvents.edges.map(edge => edge.node))}
          nextEvents={data && data.event && (
              data.event.nextEvents.edges.map(edge => edge.node))}
        />
    );
}

function NotificationLogRouteComponent() {

    //  Here we will parse application names from the url filter if any.

    const { error, data, loading } = useQuery(GetNotificationsQuery, {
        pollInterval: 5000,
    });

    return (
        <LogViewer
          currentEvent={null}
          previousEvents={data && data.notifications && (
              data.notifications.edges.filter(
                  edge => !!edge.node.event
              ).map(edge => edge.node.event))}
          nextEvents={null}
        />
    );
}

function App() {
    return (
        <Container fixed>

          <Box my={2}>
            <Button
              variant="text"
              color="primary"
              startIcon={<ChevronLeftIcon/>}
              component={RouterLink}
              to="/notifications/"
            >
              all notifications
            </Button>

            <Divider />
          </Box>

          {/* TODO: We actually want to have both panes be handled by the same component. */}
          {/* The opposite of what we have now, one use case: */}
          {/* - prev/next buttons above the right pane's context, navigating in the right pane. */}

          {/* Also, that way we can have the left-list be md=5 and xs=hidden when no space because of right pane, until right pane is closed. */}

          {/* TODO: Add close button for right pane in that case. */}

          <Router>
            <NotificationLogRouteComponent
              path="/notifications/*"
            />
            <EventLogRouteComponent
              path="/event/:applicationName/:originatorId/:originatorVersionString/*"
            />
          </Router>

        </Container>
    );
}


function AppWithProviders() {
    return (
        <ApolloProvider client={client}>
          <App />
        </ApolloProvider>
    );
}

export default AppWithProviders;
